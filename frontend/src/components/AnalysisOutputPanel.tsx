import React, { useState } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Paper,

  Rating,
  Badge,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  BugReport as BugIcon,
  Lightbulb as LightbulbIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
} from '@mui/icons-material';
import { AnalysisResult, CriteriaResult } from '../types/analysis';

interface AnalysisOutputPanelProps {
  result: AnalysisResult | null;
  loading: boolean;
  error: string | null;
}



const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical': return <ErrorIcon />;
    case 'high': return <WarningIcon />;
    case 'medium': return <InfoIcon />;
    case 'low': return <CheckIcon />;
    default: return <InfoIcon />;
  }
};

const getScoreColor = (score: number): 'error' | 'warning' | 'info' | 'success' => {
  if (score >= 8) return 'success';
  if (score >= 6) return 'info';
  if (score >= 4) return 'warning';
  return 'error';
};

const CriteriaCard: React.FC<{ criteria: CriteriaResult }> = ({ criteria }) => (
  <Card variant="outlined" sx={{ mb: 2 }}>
    <CardContent sx={{ pb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>
          {criteria.criterion}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Rating
            value={criteria.score / 2}
            precision={0.1}
            size="small"
            readOnly
          />
          <Chip
            label={`${criteria.score}/10`}
            color={getScoreColor(criteria.score) as any}
            size="small"
            icon={getSeverityIcon(criteria.severity)}
          />
        </Box>
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {criteria.feedback}
      </Typography>
      
      {criteria.suggestions.length > 0 && (
        <Accordion variant="outlined">
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              Suggestions ({criteria.suggestions.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {criteria.suggestions.map((suggestion, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <LightbulbIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={suggestion} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
    </CardContent>
  </Card>
);

const MetricsGrid: React.FC<{ metrics: any }> = ({ metrics }) => (
  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2, mb: 3 }}>
    {Object.entries(metrics).map(([key, value]) => (
      <Paper key={key} sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="h4" color="primary">
          {(value as number).toFixed(1)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
          {key.replace('_', ' ')}
        </Typography>
        <LinearProgress
          variant="determinate"
          value={(value as number) * 10}
          sx={{ mt: 1 }}
          color={getScoreColor(value as number)}
        />
      </Paper>
    ))}
  </Box>
);

const AnalysisOutputPanel: React.FC<AnalysisOutputPanelProps> = ({
  result,
  loading,
  error,
}) => {
  const [expandedSections, setExpandedSections] = useState<string[]>(['summary']);

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleExport = () => {
    if (!result) return;
    
    const exportData = {
      ...result,
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
    if (!result) return;
    
    const shareText = `Code Analysis Results\n\nOverall Score: ${result.overall_score}/10\n\nSummary: ${result.summary}`;
    
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
        
        {result && (
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

        {result && (
          <>
            {/* Overall Score */}
            <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent sx={{ color: 'white' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h4">
                      {result.overall_score.toFixed(1)}/10
                    </Typography>
                    <Typography variant="h6">
                      Overall Code Quality
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="caption">
                      Analyzed in {result.processing_time_ms}ms
                    </Typography>
                    <br />
                    <Typography variant="caption">
                      {new Date(result.analysis_timestamp).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>

            {/* Summary */}
            <Accordion
              expanded={expandedSections.includes('summary')}
              onChange={() => handleSectionToggle('summary')}
              sx={{ mb: 2 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Executive Summary</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography>{result.summary}</Typography>
              </AccordionDetails>
            </Accordion>

            {/* Code Quality Metrics */}
            {result.code_quality_metrics && (
              <Accordion
                expanded={expandedSections.includes('metrics')}
                onChange={() => handleSectionToggle('metrics')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Quality Metrics</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <MetricsGrid metrics={result.code_quality_metrics} />
                </AccordionDetails>
              </Accordion>
            )}

            {/* Criteria Results */}
            <Accordion
              expanded={expandedSections.includes('criteria')}
              onChange={() => handleSectionToggle('criteria')}
              sx={{ mb: 2 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">
                  Detailed Criteria Analysis ({result.criteria_results.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {result.criteria_results.map((criteria, index) => (
                  <CriteriaCard key={index} criteria={criteria} />
                ))}
              </AccordionDetails>
            </Accordion>

            {/* Positive Aspects */}
            {result.positive_aspects.length > 0 && (
              <Accordion
                expanded={expandedSections.includes('positive')}
                onChange={() => handleSectionToggle('positive')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    <Badge badgeContent={result.positive_aspects.length} color="success">
                      Positive Aspects
                    </Badge>
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.positive_aspects.map((aspect, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckIcon color="success" />
                        </ListItemIcon>
                        <ListItemText primary={aspect} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Areas for Improvement */}
            {result.areas_for_improvement.length > 0 && (
              <Accordion
                expanded={expandedSections.includes('improvements')}
                onChange={() => handleSectionToggle('improvements')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    <Badge badgeContent={result.areas_for_improvement.length} color="warning">
                      Areas for Improvement
                    </Badge>
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.areas_for_improvement.map((area, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <TrendingUpIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText primary={area} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Recommendations */}
            {result.recommendations.length > 0 && (
              <Accordion
                expanded={expandedSections.includes('recommendations')}
                onChange={() => handleSectionToggle('recommendations')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Recommendations ({result.recommendations.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.recommendations.map((recommendation, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <LightbulbIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={recommendation} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Detected Patterns */}
            {result.detected_patterns.length > 0 && (
              <Accordion
                expanded={expandedSections.includes('patterns')}
                onChange={() => handleSectionToggle('patterns')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Detected Patterns ({result.detected_patterns.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {result.detected_patterns.map((pattern, index) => (
                      <Chip key={index} label={pattern} variant="outlined" />
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Potential Issues */}
            {result.potential_issues.length > 0 && (
              <Accordion
                expanded={expandedSections.includes('issues')}
                onChange={() => handleSectionToggle('issues')}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    <Badge badgeContent={result.potential_issues.length} color="error">
                      Potential Issues
                    </Badge>
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.potential_issues.map((issue, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <BugIcon color="error" />
                        </ListItemIcon>
                        <ListItemText primary={issue} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}
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

export default AnalysisOutputPanel;
