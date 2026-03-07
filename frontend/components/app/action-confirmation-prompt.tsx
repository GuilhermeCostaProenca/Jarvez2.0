import { Button } from '@/components/ui/button';
import type { PendingActionConfirmation } from '@/lib/types/realtime';

interface ActionConfirmationPromptProps {
  pendingConfirmation: PendingActionConfirmation | null;
  isConfirming: boolean;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}

export function ActionConfirmationPrompt({
  pendingConfirmation,
  isConfirming,
  onConfirm,
  onCancel,
}: ActionConfirmationPromptProps) {
  if (!pendingConfirmation) {
    return null;
  }

  return (
    <div className="mx-auto mb-3 w-full max-w-2xl rounded-lg border border-amber-400/40 bg-black/70 p-3 text-xs text-amber-100 shadow-lg">
      <p className="font-semibold text-amber-200">Confirmacao de acao sensivel</p>
      <p className="mt-1 text-white/90">{pendingConfirmation.message}</p>
      <p className="mt-1 text-[11px] text-white/60">Expira em {pendingConfirmation.expiresIn}s</p>
      <div className="mt-3 flex gap-2">
        <Button type="button" size="sm" onClick={() => void onConfirm()} disabled={isConfirming}>
          {isConfirming ? 'Confirmando...' : 'Confirmar'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={onCancel}
          disabled={isConfirming}
        >
          Cancelar
        </Button>
      </div>
    </div>
  );
}
