import React from 'react';
import {
  Box,
  Typography,
  Toolbar,
  Divider,
  Alert,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Paper,
  Rating,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
} from '@mui/icons-material';

interface CriterionScore {
  score: number;
  comment: string;
}

interface SimpleAnalysisResult {
  overall_score?: number;
  summary?: string;
  detailed_feedback?: string;
  processing_time_ms?: number;
  analysis_timestamp?: string;
  input_length?: number;
  areCodeChangesOptimized?: CriterionScore;
  areCodeChangesRelative?: CriterionScore;
  isCodeFormatted?: CriterionScore;
  isCodeWellWritten?: CriterionScore;
  areCommentsWritten?: CriterionScore;
  cyclomaticComplexityScore?: CriterionScore;
  missingElements?: CriterionScore;
  loopholes?: CriterionScore;
  isCommitMessageWellWritten?: CriterionScore;
  isNamingConventionFollowed?: CriterionScore;
  areThereAnySpellingMistakes?: CriterionScore;
  securityConcernsAny?: CriterionScore;
  isCodeDuplicated?: CriterionScore;
  areConstantsDefinedCentrally?: CriterionScore;
  isCodeModular?: CriterionScore;
  isLoggingDoneProperly?: CriterionScore;
}

interface SimpleAnalysisOutputPanelProps {
  result: SimpleAnalysisResult | null;
  loading: boolean;
  error: string | null;
}

const SimpleAnalysisOutputPanel: React.FC<SimpleAnalysisOutputPanelProps> = ({
  result,
  loading,
  error,
}) => {
  // Add console log to see what we receive
  console.log('🔍 Raw result received:', result);
  
  // Function to try parsing JSON from detailed_feedback if structured data is missing
  const getStructuredData = (result: SimpleAnalysisResult): SimpleAnalysisResult => {
    if (!result) return result;
    
    console.log('🔧 Processing result in getStructuredData:', {
      hasOverallScore: result.overall_score !== undefined,
      hasSummary: !!result.summary,
      hasCriteria: !!(result.areCodeChangesOptimized || result.isCodeFormatted || result.isCodeWellWritten),
      detailedFeedbackLength: result.detailed_feedback?.length || 0
    });
    
    console.log('🔍 DEBUG: Original result from API:', result);
    
    // If we have structured data (check for criteria), use it
    const hasCriteria = result.areCodeChangesOptimized || result.isCodeFormatted || result.isCodeWellWritten;
    if (result.overall_score !== undefined && result.summary && hasCriteria) {
      console.log('✅ DEBUG: Using structured data from API');
      return result;
    }
    
    console.log('⚠️ DEBUG: Missing structured data, trying to parse from detailed_feedback');
    console.log('📝 DEBUG: detailed_feedback content:', result.detailed_feedback);
    
    // Try to parse JSON from detailed_feedback
    if (result.detailed_feedback) {
      try {
        // Look for JSON in the detailed_feedback (try multiple patterns)
        let jsonMatch = result.detailed_feedback.match(/```json\s*([\s\S]*?)\s*```/);
        
        // If no json block found, try without "json" keyword
        if (!jsonMatch) {
          jsonMatch = result.detailed_feedback.match(/```\s*(\{[\s\S]*?\})\s*```/);
        }
        
        // If still no match, try to find any JSON-like structure
        if (!jsonMatch) {
          const directJsonMatch = result.detailed_feedback.match(/(\{[\s\S]*\})/);
          if (directJsonMatch) {
            jsonMatch = [directJsonMatch[0], directJsonMatch[1]];
          }
        }
        
        console.log('🔍 DEBUG: JSON regex match result:', jsonMatch ? 'Found' : 'Not found');
        console.log('📄 DEBUG: Full detailed_feedback:', result.detailed_feedback);
        
        if (jsonMatch) {
          console.log('📋 DEBUG: Extracted JSON string:', jsonMatch[1]);
          const parsedData = JSON.parse(jsonMatch[1]);
          console.log('✅ DEBUG: Successfully parsed JSON:', parsedData);
          
          const structuredResult = {
            ...result,
            overall_score: parsedData.overall_score || result.overall_score,
            summary: parsedData.summary || result.summary,
            detailed_feedback: parsedData.detailed_feedback || result.detailed_feedback,
            // Map all 16 criteria
            areCodeChangesOptimized: parsedData.areCodeChangesOptimized || result.areCodeChangesOptimized,
            areCodeChangesRelative: parsedData.areCodeChangesRelative || result.areCodeChangesRelative,
            isCodeFormatted: parsedData.isCodeFormatted || result.isCodeFormatted,
            isCodeWellWritten: parsedData.isCodeWellWritten || result.isCodeWellWritten,
            areCommentsWritten: parsedData.areCommentsWritten || result.areCommentsWritten,
            cyclomaticComplexityScore: parsedData.cyclomaticComplexityScore || result.cyclomaticComplexityScore,
            missingElements: parsedData.missingElements || result.missingElements,
            loopholes: parsedData.loopholes || result.loopholes,
            isCommitMessageWellWritten: parsedData.isCommitMessageWellWritten || result.isCommitMessageWellWritten,
            isNamingConventionFollowed: parsedData.isNamingConventionFollowed || result.isNamingConventionFollowed,
            areThereAnySpellingMistakes: parsedData.areThereAnySpellingMistakes || result.areThereAnySpellingMistakes,
            securityConcernsAny: parsedData.securityConcernsAny || result.securityConcernsAny,
            isCodeDuplicated: parsedData.isCodeDuplicated || result.isCodeDuplicated,
            areConstantsDefinedCentrally: parsedData.areConstantsDefinedCentrally || result.areConstantsDefinedCentrally,
            isCodeModular: parsedData.isCodeModular || result.isCodeModular,
            isLoggingDoneProperly: parsedData.isLoggingDoneProperly || result.isLoggingDoneProperly
          };
          
          console.log('🎯 DEBUG: Final structured result:', structuredResult);
          return structuredResult;
        } else {
          console.log('❌ DEBUG: No JSON block found in detailed_feedback');
        }
      } catch (e) {
        console.error('❌ DEBUG: Failed to parse JSON from detailed_feedback:', e);
      }
    } else {
      console.log('❌ DEBUG: No detailed_feedback available');
    }
    
    console.log('⚠️ DEBUG: Returning original result unchanged');
    return result;
  };
  
  // Get structured data (either from API or parsed from detailed_feedback)
  const structuredResult = result ? getStructuredData(result) : null;

  // Helper function to render individual criteria
  const renderCriterion = (key: string, label: string, criterion?: CriterionScore) => {
    if (!criterion) return null;

    const getScoreColor = (score: number) => {
      if (score >= 8) return 'success';
      if (score >= 6) return 'warning';
      return 'error';
    };

    return (
      <Paper key={key} sx={{ p: 2, border: '1px solid #e0e0e0' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
            {label}
          </Typography>
          <Chip 
            label={`${criterion.score}/10`} 
            color={getScoreColor(criterion.score)} 
            size="small" 
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
        {criterion.comment && (
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
            {criterion.comment}
          </Typography>
        )}
      </Paper>
    );
  };
  
  console.log('🚀 DEBUG: Component received result:', result);
  console.log('🎯 DEBUG: Component using structuredResult:', structuredResult);
  const handleExport = () => {
    if (!structuredResult) return;
    
    const exportData = {
      ...structuredResult,
      exported_at: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code-analysis-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (!structuredResult) return;
    
    const shareText = `Code Analysis Results\n\nOverall Score: ${structuredResult.overall_score || 'N/A'}/10\n\nSummary: ${structuredResult.summary || 'No summary'}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Code Analysis Results',
          text: shareText,
        });
      } catch (err) {
        console.error('Error sharing:', err);
      }
    } else {
      navigator.clipboard.writeText(shareText);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Toolbar variant="dense" sx={{ minHeight: 48 }}>
        <Typography variant="h6" sx={{ flexGrow: 1, fontSize: '1rem' }}>
          Analysis Results
        </Typography>
        
        {structuredResult && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Export results">
              <IconButton size="small" onClick={handleExport}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share results">
              <IconButton size="small" onClick={handleShare}>
                <ShareIcon />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Toolbar>
      
      <Divider />

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {loading && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Analyzing your code with AI...
            </Typography>
            <LinearProgress sx={{ mt: 2 }} />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              This may take a few moments depending on code complexity
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="h6">Analysis Failed</Typography>
            {error}
          </Alert>
        )}

        {structuredResult && (
          <>
            {/* Overall Score */}
            {structuredResult && structuredResult.overall_score !== undefined && (
              <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <CardContent sx={{ color: 'white' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h4">
                        {structuredResult.overall_score.toFixed(1)}/10
                      </Typography>
                      <Typography variant="h6">
                        Overall Code Quality
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Rating
                        value={structuredResult.overall_score / 2}
                        precision={0.1}
                        size="large"
                        readOnly
                        sx={{ color: 'white' }}
                      />
                      {structuredResult.processing_time_ms && (
                        <Typography variant="caption" sx={{ display: 'block' }}>
                          Analyzed in {structuredResult.processing_time_ms}ms
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Summary */}
            {structuredResult && structuredResult.summary && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Summary
                  </Typography>
                  <Typography>{structuredResult.summary}</Typography>
                </CardContent>
              </Card>
            )}

            {/* Detailed Feedback */}
            {structuredResult && structuredResult.detailed_feedback && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Detailed Analysis
                  </Typography>
                  <Typography
                    sx={{
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'monospace',
                      backgroundColor: '#f5f5f5',
                      p: 2,
                      borderRadius: 1,
                      maxHeight: '300px',
                      overflow: 'auto'
                    }}
                  >
                    {structuredResult.detailed_feedback}
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Code Review Criteria */}
            {structuredResult && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckIcon color="primary" />
                    Code Review Criteria
                  </Typography>
                  
                  {/* Render criteria in a grid */}
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2, mt: 2 }}>
                    {renderCriterion('areCodeChangesOptimized', 'Are Code Changes Optimized', structuredResult.areCodeChangesOptimized)}
                    {renderCriterion('areCodeChangesRelative', 'Are Code Changes Relative', structuredResult.areCodeChangesRelative)}
                    {renderCriterion('isCodeFormatted', 'Is Code Formatted', structuredResult.isCodeFormatted)}
                    {renderCriterion('isCodeWellWritten', 'Is Code Well Written', structuredResult.isCodeWellWritten)}
                    {renderCriterion('areCommentsWritten', 'Are Comments Written', structuredResult.areCommentsWritten)}
                    {renderCriterion('cyclomaticComplexityScore', 'Cyclomatic Complexity Score', structuredResult.cyclomaticComplexityScore)}
                    {renderCriterion('missingElements', 'Missing Elements', structuredResult.missingElements)}
                    {renderCriterion('loopholes', 'Loopholes', structuredResult.loopholes)}
                    {renderCriterion('isCommitMessageWellWritten', 'Is Commit Message Well Written', structuredResult.isCommitMessageWellWritten)}
                    {renderCriterion('isNamingConventionFollowed', 'Is Naming Convention Followed', structuredResult.isNamingConventionFollowed)}
                    {renderCriterion('areThereAnySpellingMistakes', 'Are There Any Spelling Mistakes', structuredResult.areThereAnySpellingMistakes)}
                    {renderCriterion('securityConcernsAny', 'Security Concerns Any', structuredResult.securityConcernsAny)}
                    {renderCriterion('isCodeDuplicated', 'Is Code Duplicated', structuredResult.isCodeDuplicated)}
                    {renderCriterion('areConstantsDefinedCentrally', 'Are Constants Defined Centrally', structuredResult.areConstantsDefinedCentrally)}
                    {renderCriterion('isCodeModular', 'Is Code Modular', structuredResult.isCodeModular)}
                    {renderCriterion('isLoggingDoneProperly', 'Is Logging Done Properly', structuredResult.isLoggingDoneProperly)}
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Analysis Info */}
            <Paper sx={{ p: 2, backgroundColor: '#f9f9f9' }}>
              <Typography variant="caption" color="text.secondary">
                Analysis completed {structuredResult && structuredResult.analysis_timestamp && `on ${new Date(structuredResult.analysis_timestamp).toLocaleString()}`}
                {structuredResult && structuredResult.input_length && ` • Input: ${structuredResult.input_length} characters`}
                {structuredResult && structuredResult.processing_time_ms && ` • Processing time: ${structuredResult.processing_time_ms}ms`}
              </Typography>
            </Paper>
          </>
        )}

        {!result && !loading && !error && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No analysis results yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Paste your code or git diff in the left panel and click "Analyze Code" to get started.
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default SimpleAnalysisOutputPanel;
