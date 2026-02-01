/**
 * TypeScript Type Specifications for Career Intelligence Assistant.
 *
 * This file defines all frontend types/contracts BEFORE implementation.
 * These specs mirror the backend Pydantic models.
 */

// ============================================================================
// Enums
// ============================================================================

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export type SkillCategory =
  | 'programming'
  | 'framework'
  | 'tool'
  | 'soft_skill'
  | 'domain'
  | 'certification'
  | 'language';

export type RequirementType = 'must_have' | 'nice_to_have' | 'responsibility';

export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

export type RecommendationCategory =
  | 'skill_gap'
  | 'resume_improvement'
  | 'experience_highlight'
  | 'certification'
  | 'networking';

export type Priority = 'high' | 'medium' | 'low';

export type QuestionCategory = 'behavioral' | 'technical' | 'situational' | 'culture_fit';

export type Difficulty = 'easy' | 'medium' | 'hard';

export type DemandTrend = 'increasing' | 'stable' | 'decreasing';

// ============================================================================
// Core Data Models
// ============================================================================

export interface Skill {
  name: string;
  category: SkillCategory;
  level: SkillLevel;
  yearsExperience?: number;
}

export interface Experience {
  title: string;
  company: string;
  duration: string;
  durationMonths?: number;
  description?: string;
  skillsUsed: string[];
}

export interface Education {
  degree: string;
  institution: string;
  year?: number;
  gpa?: number;
  fieldOfStudy?: string;
}

export interface Requirement {
  text: string;
  type: RequirementType;
  skills: string[];
}

// ============================================================================
// Parsed Documents
// ============================================================================

export interface ParsedResume {
  id: string;
  skills: Skill[];
  experiences: Experience[];
  education: Education[];
  certifications: string[];
  summary?: string;
  contactRedacted: boolean;
}

export interface ParsedJobDescription {
  id: string;
  title: string;
  company?: string;
  requirements: Requirement[];
  requiredSkills: Skill[];
  niceToHaveSkills: Skill[];
  experienceYearsMin?: number;
  experienceYearsMax?: number;
  educationRequirements: string[];
  responsibilities: string[];
  cultureSignals: string[];
}

// ============================================================================
// Analysis Results
// ============================================================================

export interface SkillMatch {
  skillName: string;
  resumeLevel: SkillLevel;
  requiredLevel?: SkillLevel;
  matchQuality: 'exact' | 'partial' | 'exceeds';
}

export interface MissingSkill {
  skillName: string;
  importance: 'must_have' | 'nice_to_have';
  difficultyToAcquire: Difficulty;
}

export interface JobMatch {
  jobId: string;
  resumeId: string;
  jobTitle: string;
  company?: string;
  fitScore: number; // 0-100
  skillMatchScore: number;
  experienceMatchScore: number;
  educationMatchScore: number;
  matchingSkills: SkillMatch[];
  missingSkills: MissingSkill[];
  transferableSkills: string[];
}

export interface AnalysisResult {
  sessionId: string;
  status: 'completed' | 'in_progress' | 'failed';
  jobMatches: JobMatch[];
  completedAt?: string;
}

// ============================================================================
// Recommendations
// ============================================================================

export interface Recommendation {
  id: string;
  category: RecommendationCategory;
  priority: Priority;
  title: string;
  description: string;
  actionItems: string[];
  estimatedTime?: string;
  resources: string[];
}

export interface RecommendationResult {
  sessionId: string;
  jobId?: string;
  recommendations: Recommendation[];
  priorityOrder: string[];
  estimatedImprovement?: number;
}

// ============================================================================
// Interview Prep
// ============================================================================

export interface STARExample {
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  category: QuestionCategory;
  difficulty: Difficulty;
  whyAsked?: string;
  suggestedAnswer: string;
  starExample?: STARExample;
  relatedExperience?: string;
}

export interface WeaknessResponse {
  weakness: string;
  honestResponse: string;
  mitigation: string;
}

export interface InterviewPrepResult {
  sessionId: string;
  jobId?: string;
  questions: InterviewQuestion[];
  talkingPoints: string[];
  weaknessResponses: WeaknessResponse[];
  questionsToAsk: string[];
}

// ============================================================================
// Market Insights
// ============================================================================

export interface SalaryRange {
  min: number;
  max: number;
  median: number;
  currency: string;
  locationAdjusted: boolean;
}

export interface CareerPath {
  title: string;
  typicalYearsToReach: number;
  requiredSkills: string[];
  salaryIncreasePercent?: number;
}

export interface MarketInsights {
  salaryRange: SalaryRange;
  demandTrend: DemandTrend;
  topSkillsInDemand: string[];
  careerPaths: CareerPath[];
  industryInsights: string;
  competitiveLandscape?: string;
  dataFreshness: string;
}

export interface MarketInsightsResult {
  sessionId: string;
  jobId?: string;
  insights: MarketInsights;
}

// ============================================================================
// Session
// ============================================================================

export interface Session {
  sessionId: string;
  createdAt: string;
  expiresAt: string;
}

export interface SessionState {
  session: Session | null;
  resume: ParsedResume | null;
  jobDescriptions: ParsedJobDescription[];
  analysisResult: AnalysisResult | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Agent Messages (WebSocket)
// ============================================================================

export interface AgentStatusUpdate {
  agentName: string;
  status: AgentStatus;
  progress: number; // 0-100
  currentStep?: string;
  error?: string;
}

export interface AgentMessage {
  messageId: string;
  timestamp: string;
  sourceAgent: string;
  targetAgent?: string;
  messageType: 'request' | 'response' | 'error' | 'status';
  payload: Record<string, unknown>;
  correlationId: string;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface ResumeUploadResponse {
  resumeId: string;
  status: 'parsed' | 'error';
  skills: Skill[];
  experiences: Experience[];
  education: Education[];
  summary?: string;
  piiRedacted: boolean;
}

export interface JobDescriptionUploadResponse {
  jobId: string;
  status: 'parsed' | 'error';
  title: string;
  company?: string;
  requirements: Requirement[];
  requiredSkills: Skill[];
  niceToHaveSkills: Skill[];
}

export interface AnalyzeRequest {
  sessionId: string;
}

export interface AnalysisStartedResponse {
  analysisId: string;
  status: 'started' | 'queued';
  websocketUrl: string;
  estimatedDurationSeconds?: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  dependencies: Record<string, 'connected' | 'disconnected' | 'available' | 'unavailable'>;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Wizard State
// ============================================================================

export type WizardStep = 1 | 2 | 3 | 4;

export interface WizardState {
  currentStep: WizardStep;
  canProceed: boolean;
  isAnalyzing: boolean;
  agentStatuses: AgentStatusUpdate[];
}

// ============================================================================
// File Upload
// ============================================================================

export interface FileUploadState {
  file: File | null;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}

export const ALLOWED_FILE_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
export const MAX_FILE_SIZE_MB = 10;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

// ============================================================================
// Chat
// ============================================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  jobId?: string;
}

export interface ChatResponse {
  response: string;
  suggestedQuestions: string[];
}

// ============================================================================
// API Configuration
// ============================================================================

export interface ApiConfig {
  baseUrl: string;
  wsUrl: string;
  timeout: number;
}

export const DEFAULT_API_CONFIG: ApiConfig = {
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  timeout: 30000,
};
