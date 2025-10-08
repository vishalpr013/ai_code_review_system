export interface CriteriaResult {
  criterion: string;
  score: number;
  feedback: string;
  suggestions: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AnalysisResult {
  overall_score: number;
  summary: string;
  criteria_results: CriteriaResult[];
  recommendations: string[];
  positive_aspects: string[];
  areas_for_improvement: string[];
  code_quality_metrics: {
    complexity: number;
    maintainability: number;
    readability: number;
    testability: number;
  };
  detected_patterns: string[];
  potential_issues: string[];
  analysis_timestamp: string;
  processing_time_ms: number;
}

export interface GitDiffInfo {
  file_path: string;
  change_type: 'added' | 'modified' | 'deleted' | 'renamed';
  lines_added: number;
  lines_removed: number;
  hunks: GitDiffHunk[];
}

export interface GitDiffHunk {
  old_start: number;
  old_lines: number;
  new_start: number;
  new_lines: number;
  lines: GitDiffLine[];
}

export interface GitDiffLine {
  type: 'context' | 'added' | 'removed';
  line_number_old?: number;
  line_number_new?: number;
  content: string;
}

export interface CodeAnalysisRequest {
  code: string;
  format?: 'git-diff' | 'raw-code';
  language?: string;
  context?: string;
}

export interface ErrorResponse {
  error: string;
  details?: string;
  timestamp: string;
}
