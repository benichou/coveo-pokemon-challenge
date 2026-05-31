// Mirror of rga-eval/src/schemas.py — keep these in sync.
// (Pydantic on the producer side, plain TS on the consumer side.)

export type LayerStats = {
  accuracy: number;
  precision: number;
  hard_recall: number;
  citation_precision: number;
  n_questions: number;
};

export type JudgeVerdict = {
  is_correct: boolean;
  has_hallucination: boolean;
  false_claims: string[];
  reasoning: string;
};

export type PerQuestionResult = {
  question_id: string;
  question: string;
  layer: 1 | 2 | 3;
  category: string;
  rga_fired: boolean;
  answer_text: string;
  cited_uris: string[];
  hard_recall: number;
  citation_precision: number;
  verdict: JudgeVerdict;
};

export type EvalRun = {
  timestamp: string;
  coveo_org_id: string;
  judge_model: string;
  overall: LayerStats;
  by_layer: Record<"1" | "2" | "3", LayerStats>;
  per_question: PerQuestionResult[];
};

export type EvalRunWithMeta = EvalRun & {
  // Date string extracted from the filename (YYYY-MM-DD).
  date: string;
  // Source filename for debugging.
  filename: string;
};
