import { useState } from 'react';
import { Pencil, CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { CorrectionDialog } from './CorrectionDialog';
import type { VLMClassification, ClassificationStatus } from '../types/inspection';

interface ReportEditorProps {
  vin: string;
  clientTraceId: string;
  classifications: Record<string, VLMClassification>;
  frameReferences: Array<{ filename: string; sha256: string }>;
  authToken: string;
  onCorrectionSubmitted?: () => void;
}

const ITEM_NAMES: Record<string, string> = {
  tires_wheels: 'Tires & Wheels',
  bucket_attachment: 'Bucket Attachment',
  lift_arms_pins: 'Lift Arms & Pins',
  hoses_lines_leaks: 'Hoses & Lines',
  articulation_driveline: 'Articulation & Driveline',
  undercarriage_leaks: 'Undercarriage',
  cooling_airflow: 'Cooling & Airflow',
  cab_body_glass: 'Cab, Body & Glass',
  steps_holds: 'Steps & Handholds',
  engine_bay_leaks_debris: 'Engine Bay',
};

const statusConfig: Record<ClassificationStatus, { icon: typeof CheckCircle2; color: string; bg: string }> = {
  PASS: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
  MONITOR: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  FAIL: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
  UNKNOWN: { icon: HelpCircle, color: 'text-gray-400', bg: 'bg-gray-500/10 border-gray-500/20' },
};

export function ReportEditor({
  vin,
  clientTraceId,
  classifications,
  frameReferences,
  authToken,
  onCorrectionSubmitted,
}: ReportEditorProps) {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  const selectedClassification = selectedItem ? classifications[selectedItem] : null;
  const primaryFrame = frameReferences[0];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Inspection Report</h2>
          <p className="text-sm text-zinc-400">VIN: {vin}</p>
        </div>
        <Badge variant="outline" className="text-zinc-400 border-zinc-600">
          {Object.keys(classifications).length} items classified
        </Badge>
      </div>

      <div className="grid gap-3">
        {Object.entries(classifications).map(([itemId, classification]) => {
          const name = ITEM_NAMES[itemId] || itemId.replace(/_/g, ' ');
          const status = classification.status as ClassificationStatus;
          const config = statusConfig[status] || statusConfig.UNKNOWN;
          const Icon = config.icon;

          return (
            <div
              key={itemId}
              className={`p-4 rounded-xl border ${config.bg} transition-all hover:border-zinc-600`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className={`p-2 rounded-lg ${config.bg}`}>
                    <Icon size={18} className={config.color} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-white">{name}</span>
                      <Badge
                        variant="outline"
                        className={`text-xs ${config.color} border-current/30`}
                      >
                        {status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-zinc-500">
                      <span>Score: {classification.score.toFixed(2)}</span>
                      <span>Confidence: {(classification.confidence * 100).toFixed(0)}%</span>
                    </div>
                    {classification.reasoning && (
                      <p className="text-sm text-zinc-400 mt-2 line-clamp-2">
                        {classification.reasoning}
                      </p>
                    )}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedItem(itemId)}
                  className="text-zinc-400 hover:text-yellow-400 hover:bg-yellow-500/10"
                >
                  <Pencil size={16} />
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3 pt-4 border-t border-zinc-800">
        {(['PASS', 'MONITOR', 'FAIL'] as ClassificationStatus[]).map((status) => {
          const count = Object.values(classifications).filter(
            (c) => c.status === status
          ).length;
          const config = statusConfig[status];
          const Icon = config.icon;

          return (
            <div
              key={status}
              className={`p-3 rounded-lg ${config.bg} text-center`}
            >
              <Icon size={20} className={`${config.color} mx-auto mb-1`} />
              <p className="text-2xl font-bold text-white">{count}</p>
              <p className="text-xs text-zinc-400">{status}</p>
            </div>
          );
        })}
      </div>

      {/* Correction Dialog */}
      {selectedItem && selectedClassification && (
        <CorrectionDialog
          open={!!selectedItem}
          onOpenChange={(open) => !open && setSelectedItem(null)}
          itemId={selectedItem}
          itemName={ITEM_NAMES[selectedItem] || selectedItem}
          vin={vin}
          clientTraceId={clientTraceId}
          classification={selectedClassification}
          frameSha256={primaryFrame?.sha256 || ''}
          frameFilename={primaryFrame?.filename}
          authToken={authToken}
          onSuccess={onCorrectionSubmitted}
        />
      )}
    </div>
  );
}
