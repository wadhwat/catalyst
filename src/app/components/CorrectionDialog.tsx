import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import type { VLMClassification, CorrectionRequest, ClassificationStatus } from '../types/inspection';
import { useCorrections } from '../hooks/useCorrections';

interface CorrectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  itemId: string;
  itemName: string;
  vin: string;
  clientTraceId: string;
  classification: VLMClassification;
  frameSha256: string;
  frameFilename?: string;
  authToken: string;
  onSuccess?: () => void;
}

const STATUS_OPTIONS: ClassificationStatus[] = ['PASS', 'MONITOR', 'FAIL'];

const statusColors: Record<ClassificationStatus, string> = {
  PASS: 'bg-green-500/20 text-green-400 border-green-500/30',
  MONITOR: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  FAIL: 'bg-red-500/20 text-red-400 border-red-500/30',
  UNKNOWN: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const scoreFromStatus = (status: ClassificationStatus): number => {
  switch (status) {
    case 'PASS':
      return 0.15;
    case 'MONITOR':
      return 0.45;
    case 'FAIL':
      return 0.75;
    default:
      return 0.5;
  }
};

export function CorrectionDialog({
  open,
  onOpenChange,
  itemId,
  itemName,
  vin,
  clientTraceId,
  classification,
  frameSha256,
  frameFilename,
  authToken,
  onSuccess,
}: CorrectionDialogProps) {
  const [correctedStatus, setCorrectedStatus] = useState<ClassificationStatus>(classification.status as ClassificationStatus);
  const [correctedScore, setCorrectedScore] = useState(classification.score);
  const [notes, setNotes] = useState('');
  const { loading, error, submitCorrection } = useCorrections();

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setCorrectedStatus(classification.status as ClassificationStatus);
      setCorrectedScore(classification.score);
      setNotes('');
    }
  }, [open, classification]);

  // Update score when status changes
  useEffect(() => {
    setCorrectedScore(scoreFromStatus(correctedStatus));
  }, [correctedStatus]);

  const handleSubmit = async () => {
    const correction: CorrectionRequest = {
      item_id: itemId,
      vin,
      client_trace_id: clientTraceId,
      original_status: classification.status,
      original_score: classification.score,
      original_confidence: classification.confidence,
      original_reasoning: classification.reasoning,
      corrected_status: correctedStatus,
      corrected_score: correctedScore,
      correction_notes: notes,
      frame_sha256: frameSha256,
      frame_filename: frameFilename,
    };

    const result = await submitCorrection(correction, authToken);
    if (result) {
      onOpenChange(false);
      onSuccess?.();
    }
  };

  const isValid = notes.length >= 10 && correctedStatus !== classification.status;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-zinc-900 border-zinc-700 text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white">Edit Classification</DialogTitle>
          <DialogDescription className="text-zinc-400">
            Correct the AI classification for <span className="font-semibold text-zinc-300">{itemName}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Original Classification */}
          <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Original AI Classification</p>
            <div className="flex items-center gap-2">
              <Badge className={statusColors[classification.status as ClassificationStatus]}>
                {classification.status}
              </Badge>
              <span className="text-zinc-400 text-sm">
                Score: {classification.score.toFixed(2)} | Confidence: {(classification.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {classification.reasoning && (
              <p className="text-zinc-400 text-sm mt-2">{classification.reasoning}</p>
            )}
          </div>

          {/* Corrected Status */}
          <div>
            <label className="text-sm text-zinc-400 block mb-2">Corrected Status</label>
            <div className="flex gap-2">
              {STATUS_OPTIONS.map((status) => (
                <button
                  key={status}
                  onClick={() => setCorrectedStatus(status)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    correctedStatus === status
                      ? statusColors[status] + ' border-current'
                      : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>

          {/* Score Display */}
          <div>
            <label className="text-sm text-zinc-400 block mb-2">Score</label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={correctedScore}
                onChange={(e) => setCorrectedScore(parseFloat(e.target.value))}
                className="flex-1 accent-yellow-500"
              />
              <span className="text-zinc-300 font-mono w-12 text-right">
                {correctedScore.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Correction Notes */}
          <div>
            <label className="text-sm text-zinc-400 block mb-2">
              Explanation <span className="text-zinc-500">(min 10 characters)</span>
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Explain why this classification is incorrect..."
              rows={3}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-3 text-white placeholder:text-zinc-500 focus:outline-none focus:border-yellow-500/50"
            />
            <p className="text-xs text-zinc-500 mt-1">
              {notes.length}/10 characters minimum
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || loading}
            className="bg-yellow-500 text-black hover:bg-yellow-400 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Correction'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
