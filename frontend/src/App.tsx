import React, { useState, useCallback } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Box,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Snackbar,
  useMediaQuery,
} from '@mui/material';
import {
  Code as CodeIcon,
  Help as HelpIcon,
  GitHub as GitHubIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { Allotment } from 'allotment';
import 'allotment/dist/style.css';

import {
  CodeInputPanel,
  HelpDialog,
  SettingsDialog,
  CriteriaSelector,
} from './components';
import SimpleAnalysisOutputPanel from './components/SimpleAnalysisOutputPanel';
import './App.css';

interface CriterionScore {
  score: number;
  comment: string;
}

interface CriteriaConfig {
  areCodeChangesOptimized: boolean;
  areCodeChangesRelative: boolean;
  isCodeFormatted: boolean;
  isCodeWellWritten: boolean;
  areCommentsWritten: boolean;
  cyclomaticComplexityScore: boolean;
  missingElements: boolean;
  loopholes: boolean;
  isCommitMessageWellWritten: boolean;
  isNamingConventionFollowed: boolean;
  areThereAnySpellingMistakes: boolean;
  securityConcernsAny: boolean;
  isCodeDuplicated: boolean;
  areConstantsDefinedCentrally: boolean;
  isCodeModular: boolean;
  isLoggingDoneProperly: boolean;
}

interface SimpleAnalysisResult {
  overall_score?: number;
  weighted_overall_score?: number;
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

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      dark: '#115293',
      light: '#42a5f5',
    },
    secondary: {
      main: '#dc004e',
      dark: '#9a0036',
      light: '#ff5983',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  const [codeInput, setCodeInput] = useState('');
  const [prompt, setPrompt] = useState(`Analyze this code and provide a comprehensive review:

Please evaluate each criterion and provide your analysis in this JSON format:
{
    "overall_score": <number 0-10>,
    "summary": "<brief summary>",
    "detailed_feedback": "<detailed analysis>",
    "areCodeChangesOptimized": {"score": <0-10>, "comment": "<explanation>"},
    "areCodeChangesRelative": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeFormatted": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeWellWritten": {"score": <0-10>, "comment": "<explanation>"},
    "areCommentsWritten": {"score": <0-10>, "comment": "<explanation>"},
    "cyclomaticComplexityScore": {"score": <0-10>, "comment": "<explanation>"},
    "missingElements": {"score": <0-10>, "comment": "<explanation>"},
    "loopholes": {"score": <0-10>, "comment": "<explanation>"},
    "isCommitMessageWellWritten": {"score": <0-10>, "comment": "<explanation>"},
    "isNamingConventionFollowed": {"score": <0-10>, "comment": "<explanation>"},
    "areThereAnySpellingMistakes": {"score": <0-10>, "comment": "<explanation>"},
    "securityConcernsAny": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeDuplicated": {"score": <0-10>, "comment": "<explanation>"},
    "areConstantsDefinedCentrally": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeModular": {"score": <0-10>, "comment": "<explanation>"},
    "isLoggingDoneProperly": {"score": <0-10>, "comment": "<explanation>"}
}

Focus on code quality, security, performance, and best practices. Score each criterion from 0-10 where 10 is excellent.`);
  const [analysisResult, setAnalysisResult] = useState<SimpleAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Configuration for criteria analysis - start with all disabled
  const [config, setConfig] = useState<CriteriaConfig>({
    areCodeChangesOptimized: false,
    areCodeChangesRelative: false,
    isCodeFormatted: false,
    isCodeWellWritten: false,
    areCommentsWritten: false,
    cyclomaticComplexityScore: false,
    missingElements: false,
    loopholes: false,
    isCommitMessageWellWritten: false,
    isNamingConventionFollowed: false,
    areThereAnySpellingMistakes: false,
    securityConcernsAny: false,
    isCodeDuplicated: false,
    areConstantsDefinedCentrally: false,
    isCodeModular: false,
    isLoggingDoneProperly: false,
  });

  // Toggle function for criteria
  const toggleCriterion = useCallback((key: keyof CriteriaConfig) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleAnalyze = useCallback(async (code: string, customPrompt: string) => {
    if (!code.trim()) {
      setError('Please enter some code or git diff to analyze');
      return;
    }

    // Check if at least one criterion is selected
    const selectedCriteria = Object.values(config).filter(Boolean).length;
    if (selectedCriteria === 0) {
      setError('Please select at least one analysis criterion before running the analysis');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const response = await fetch('http://localhost:5001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, prompt: customPrompt, config }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.details || errorData.error || `Analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
      setSnackbarMessage('Analysis completed successfully!');
      setSnackbarOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [config]);

  const handleClearAll = useCallback(() => {
    setCodeInput('');
    setAnalysisResult(null);
    setError(null);
    setSnackbarMessage('All content cleared');
    setSnackbarOpen(true);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Header */}
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <CodeIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              AI Code Review Assistant
            </Typography>
            
            <Tooltip title="Help & Documentation">
              <IconButton
                color="inherit"
                onClick={() => setHelpOpen(true)}
                sx={{ mr: 1 }}
              >
                <HelpIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Settings">
              <IconButton
                color="inherit"
                onClick={() => setSettingsOpen(true)}
                sx={{ mr: 1 }}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="View on GitHub">
              <IconButton
                color="inherit"
                href="https://github.com"
                target="_blank"
              >
                <GitHubIcon />
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          {isMobile ? (
            // Mobile layout - stacked with compact criteria selector
            <Container maxWidth={false} sx={{ height: '100%', p: 1 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 1 }}>
                {/* Criteria Selector - Compact */}
                <Box sx={{ flexShrink: 0 }}>
                  <CriteriaSelector config={config} onToggle={toggleCriterion} />
                </Box>
                
                <Paper sx={{ 
                  flex: 3, 
                  minHeight: '45%',
                  display: 'flex',
                  flexDirection: 'column'
                }}>
                  <CodeInputPanel
                    value={codeInput}
                    onChange={setCodeInput}
                    prompt={prompt}
                    onPromptChange={setPrompt}
                    onAnalyze={handleAnalyze}
                    onClear={handleClearAll}
                    loading={loading}
                    error={error}
                  />
                </Paper>
                <Paper sx={{ 
                  flex: 2, 
                  minHeight: '35%',
                  display: 'flex',
                  flexDirection: 'column'
                }}>
                  <SimpleAnalysisOutputPanel
                    result={analysisResult}
                    loading={loading}
                    error={error}
                  />
                </Paper>
              </Box>
            </Container>
          ) : (
            // Desktop layout - split panes with criteria selector
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* Criteria Selector - Compact Header */}
              <Box sx={{ px: 2, pt: 1, pb: 0 }}>
                <CriteriaSelector config={config} onToggle={toggleCriterion} />
              </Box>
              
              {/* Split Panes - Takes remaining space */}
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <Allotment defaultSizes={[50, 50]}>
                  <Allotment.Pane minSize={300}>
                    <Paper sx={{ 
                      height: '100%', 
                      m: 2, 
                      mr: 1,
                      mt: 1,
                      display: 'flex',
                      flexDirection: 'column'
                    }}>
                      <CodeInputPanel
                        value={codeInput}
                        onChange={setCodeInput}
                        prompt={prompt}
                        onPromptChange={setPrompt}
                        onAnalyze={handleAnalyze}
                        onClear={handleClearAll}
                        loading={loading}
                        error={error}
                      />
                    </Paper>
                  </Allotment.Pane>
                  <Allotment.Pane minSize={300}>
                    <Paper sx={{ 
                      height: '100%', 
                      m: 2, 
                      ml: 1,
                      mt: 1,
                      display: 'flex',
                      flexDirection: 'column'
                    }}>
                      <SimpleAnalysisOutputPanel
                        result={analysisResult}
                        loading={loading}
                        error={error}
                      />
                    </Paper>
                  </Allotment.Pane>
                </Allotment>
              </Box>
            </Box>
          )}
        </Box>

        {/* Loading Overlay */}
        {loading && (
          <Box
            sx={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 9999,
            }}
          >
            <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress />
              <Typography>Analyzing code with AI...</Typography>
            </Paper>
          </Box>
        )}

        {/* Dialogs */}
        <HelpDialog open={helpOpen} onClose={() => setHelpOpen(false)} />
        <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={3000}
          onClose={() => setSnackbarOpen(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setSnackbarOpen(false)}
            severity="success"
            variant="filled"
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default App;
