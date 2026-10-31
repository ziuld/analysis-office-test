"""One shared reservation ledger for all calls of a review, including Akira."""
import time
import hashlib
from arktic_office.config.models import integer, runtime_options
from arktic_office.core.errors import AuditError
from arktic_office.storage.jsonio import write_json


class Budget:
    def __init__(self, invoke, output):
        self.invoke, self.output = invoke, output
        self.started = time.monotonic()
        self.calls = []
        self.seen_lines = set()
        self.stop_reason = None
        output_cap = runtime_options()['max_tokens']
        # Same worst-case output allocation as the previous 29 specialist + 2 Akira calls.
        baseline_output = 29 * output_cap + 2 * min(output_cap, 6000)
        self.limits = {'calls': integer('AUDIT_REVIEW_MAX_CALLS', 31, 1, 31),
                       'output_tokens': integer('AUDIT_REVIEW_OUTPUT_TOKENS', baseline_output, 1000, baseline_output),
                       'seconds': integer('AUDIT_REVIEW_SECONDS', 7440, 60, 7440),
                       'context_bytes': integer('AUDIT_REVIEW_CONTEXT_BYTES', 8000000, 1000, 8000000)}

    def save(self):
        write_json(self.output / 'metrics.json', {'limits': self.limits, 'calls': self.calls,
                   'charged_output_tokens': self.charged_output_tokens(),
                   'duration_seconds': round(time.monotonic() - self.started, 3), 'stop_reason': self.stop_reason,
                   'limitation': 'Reserva de salida por llamada; no es un corte remoto exacto. Tokens reales solo si los comunica el proveedor.'})

    def charged_output_tokens(self):
        total = 0
        for call in self.calls:
            usage = call.get('usage')
            actual = usage.get('output_tokens') if isinstance(usage, dict) else None
            total += max(call['reserved_output_tokens'], actual if type(actual) is int and actual >= 0 else 0)
        return total

    def __call__(self, prompt, config):
        from arktic_office.preparation.repository import redact
        elapsed = time.monotonic() - self.started
        reserved = self.charged_output_tokens()
        size = len(prompt.encode())
        tokens = config.get('max_output_tokens', 4500)
        if self.stop_reason or len(self.calls) >= self.limits['calls'] or reserved + tokens > self.limits['output_tokens'] or elapsed >= self.limits['seconds'] or sum(c['prompt_bytes'] for c in self.calls) + size > self.limits['context_bytes']:
            self.stop_reason = self.stop_reason or 'Presupuesto global agotado; se conservan las aportaciones válidas.'
            self.save()
            raise AuditError(self.stop_reason)
        lines = prompt.splitlines(keepends=True)
        repeated = sum(len(line.encode()) for line in lines if line in self.seen_lines)
        self.seen_lines.update(lines)
        record = {'agent': config.get('id'), 'model': config['model'], 'reasoning': config.get('reasoning'), 'prompt_bytes': size,
                  'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'repeated_context_bytes': repeated,
                  'reserved_output_tokens': tokens, 'usage': None, 'status': 'running'}
        self.calls.append(record)
        self.save()
        started = time.monotonic()
        try:
            result = self.invoke(prompt, {**config, 'timeout': min(config.get('timeout', 240), self.limits['seconds'] - elapsed)})
            record.update(usage=result.get('usage'), status='complete')
            return result
        except AuditError as exc:
            record.update(status='error', error=redact(str(exc)))
            # A transport failure leaves remote outcome unknown; never call again automatically.
            if getattr(exc, 'global_stop', False):
                self.stop_reason = 'Llamada interrumpida: ' + redact(str(exc)) + ' Se requiere comprobar proveedor/acceso antes de continuar.'
            raise
        finally:
            record['duration_seconds'] = round(time.monotonic() - started, 3)
            self.save()
