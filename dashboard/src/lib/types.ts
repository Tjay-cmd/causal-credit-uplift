/** Shared TypeScript shapes for dashboard JSON (phase1.json / phase2.json). */

export type QiniPoint = {
  fraction: number;
  qini: number;
  random: number;
};

export type ModelMetrics = {
  model: string;
  qini_coefficient: number;
  uplift_at_10pct: number;
  uplift_at_30pct: number;
  uplift_at_50pct: number;
  curve: QiniPoint[];
};

export type SegmentProfile = {
  model: string;
  segment: string;
  n: number;
  mean_predicted_cate: number;
  median_predicted_cate: number;
  obs_visit_rate_treated: number;
  obs_visit_rate_control: number;
  obs_uplift: number;
  share_negative_cate: number;
  recency_mean: number;
  recency_median: number;
  history_mean: number;
  history_median: number;
  mens_rate: number;
  womens_rate: number;
  newbie_rate: number;
  history_segment_mode: string;
  history_segment_mode_share: number;
  zip_code_mode: string;
  zip_code_mode_share: number;
  channel_mode: string;
  channel_mode_share: number;
};

export type CategoryGap = {
  feature: string;
  level: string;
  neg_share: number;
  test_share: number;
  gap_pp: number;
};

export type Phase1Data = {
  meta: {
    phase: number;
    title: string;
    framing: string;
    n_test: number;
  };
  models: ModelMetrics[];
  segment_profiles: SegmentProfile[];
  model_overlap: {
    overlap_share: number;
    jaccard: number;
    n_intersection: number;
    n_top: number;
    agreement_flag: string;
  };
  negative_cate: {
    n_negative: number;
    n_test: number;
    share_of_test: number;
    mean_predicted_cate: number;
    history_mean_neg: number;
    history_mean_test: number;
    category_gaps: CategoryGap[];
    framing: string;
  };
};

export type GenerationSegment = {
  segment: string;
  n: number;
  share: number;
  mean_true_cate: number;
  obs_gap: number;
  mean_baseline_prob: number;
  traits: string;
};

export type CateBySegment = {
  segment: string;
  mean_true_cate: number;
  t_learner: number;
  causal_forest: number;
  n: number;
};

export type Phase2Data = {
  meta: {
    phase: number;
    title: string;
    framing: string;
    n_test: number;
  };
  generation: {
    n_total: number;
    treatment_share: number;
    segments: GenerationSegment[];
  };
  models: ModelMetrics[];
  cate_recovery: {
    overall: Array<{
      model: string;
      pehe: number;
      corr_pred_true_cate: number;
      mean_predicted_cate: number;
      mean_true_cate: number;
      n: number;
    }>;
    by_segment: CateBySegment[];
  };
  segment_recovery: {
    composition: Array<{
      model: string;
      predicted_decile: string;
      true_segment: string;
      n: number;
      pct_of_decile: number;
      pop_share: number;
      enrichment: number;
      decile_n: number;
    }>;
    ops_summaries: Array<{
      model: string;
      top_pct_persuadables: number;
      top_pct_sleeping_dogs: number;
      deploy_line: string;
    }>;
    safer_model: string;
    safer_sleeping_dogs_rate: number;
    safer_line: string;
  };
  metric_tradeoff: {
    qini_winner: string;
    pehe_winner: string;
    contamination_safer: string;
    note: string;
  };
};

export type SegmentKey =
  | "Persuadables"
  | "Sure Things"
  | "Lost Causes"
  | "Sleeping Dogs";
