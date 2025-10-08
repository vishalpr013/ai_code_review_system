import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  TextField,
  Alert,
  Card,
  CardContent,
  Slider,
  Chip,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Palette as PaletteIcon,
  Speed as SpeedIcon,
  Code as CodeIcon,
  Restore as RestoreIcon,
} from '@mui/icons-material';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

interface Settings {
  theme: 'light' | 'dark' | 'auto';
  fontSize: number;
  autoAnalyze: boolean;
  showLineNumbers: boolean;
  enableSyntaxHighlighting: boolean;
  analysisDepth: 'basic' | 'standard' | 'comprehensive';
  apiTimeout: number;
  saveHistory: boolean;
  enableNotifications: boolean;
}

const defaultSettings: Settings = {
  theme: 'light',
  fontSize: 14,
  autoAnalyze: false,
  showLineNumbers: true,
  enableSyntaxHighlighting: true,
  analysisDepth: 'standard',
  apiTimeout: 30000,
  saveHistory: true,
  enableNotifications: true,
};

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  const [settings, setSettings] = useState<Settings>(() => {
    const saved = localStorage.getItem('codeReviewSettings');
    return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
  });

  const handleSettingChange = <K extends keyof Settings>(
    key: K,
    value: Settings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    localStorage.setItem('codeReviewSettings', JSON.stringify(settings));
    onClose();
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.removeItem('codeReviewSettings');
  };

  const getAnalysisDepthDescription = (depth: string) => {
    switch (depth) {
      case 'basic':
        return 'Quick analysis focusing on critical issues only';
      case 'standard':
        return 'Balanced analysis covering all major quality aspects';
      case 'comprehensive':
        return 'Deep analysis with detailed suggestions and examples';
      default:
        return '';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      scroll="paper"
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon />
          Settings
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {/* Appearance Settings */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PaletteIcon />
              Appearance
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel>Theme</FormLabel>
              <Select
                value={settings.theme}
                onChange={(e) => handleSettingChange('theme', e.target.value as any)}
                size="small"
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="auto">Auto (System)</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel>Font Size</FormLabel>
              <Box sx={{ px: 2, pt: 1 }}>
                <Slider
                  value={settings.fontSize}
                  onChange={(_, value) => handleSettingChange('fontSize', value as number)}
                  min={10}
                  max={20}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
                <Typography variant="caption" color="text.secondary">
                  {settings.fontSize}px
                </Typography>
              </Box>
            </FormControl>

            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showLineNumbers}
                    onChange={(e) => handleSettingChange('showLineNumbers', e.target.checked)}
                  />
                }
                label="Show line numbers"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableSyntaxHighlighting}
                    onChange={(e) => handleSettingChange('enableSyntaxHighlighting', e.target.checked)}
                  />
                }
                label="Enable syntax highlighting"
              />
            </FormGroup>
          </CardContent>
        </Card>

        {/* Analysis Settings */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CodeIcon />
              Analysis
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel>Analysis Depth</FormLabel>
              <Select
                value={settings.analysisDepth}
                onChange={(e) => handleSettingChange('analysisDepth', e.target.value as any)}
                size="small"
              >
                <MenuItem value="basic">
                  <Box>
                    <Typography>Basic</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Fast, essential checks only
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="standard">
                  <Box>
                    <Typography>Standard</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Comprehensive quality analysis
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="comprehensive">
                  <Box>
                    <Typography>Comprehensive</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Deep analysis with examples
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                {getAnalysisDepthDescription(settings.analysisDepth)}
              </Typography>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel>API Timeout</FormLabel>
              <TextField
                type="number"
                value={settings.apiTimeout / 1000}
                onChange={(e) => handleSettingChange('apiTimeout', Number(e.target.value) * 1000)}
                size="small"
                inputProps={{ min: 10, max: 120 }}
                helperText="Timeout in seconds for API requests"
              />
            </FormControl>

            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoAnalyze}
                    onChange={(e) => handleSettingChange('autoAnalyze', e.target.checked)}
                  />
                }
                label="Auto-analyze on paste"
              />
            </FormGroup>
          </CardContent>
        </Card>

        {/* Performance Settings */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SpeedIcon />
              Performance & Privacy
            </Typography>

            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.saveHistory}
                    onChange={(e) => handleSettingChange('saveHistory', e.target.checked)}
                  />
                }
                label="Save analysis history locally"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                  />
                }
                label="Enable browser notifications"
              />
            </FormGroup>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                All data is processed securely. Code is only sent to the AI service for analysis 
                and is not stored permanently.
              </Typography>
            </Alert>
          </CardContent>
        </Card>

        {/* Current Settings Summary */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Configuration
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip label={`Theme: ${settings.theme}`} size="small" />
              <Chip label={`Font: ${settings.fontSize}px`} size="small" />
              <Chip label={`Analysis: ${settings.analysisDepth}`} size="small" />
              <Chip label={`Timeout: ${settings.apiTimeout / 1000}s`} size="small" />
              {settings.autoAnalyze && <Chip label="Auto-analyze" size="small" color="primary" />}
              {settings.showLineNumbers && <Chip label="Line numbers" size="small" color="primary" />}
              {settings.enableSyntaxHighlighting && <Chip label="Syntax highlighting" size="small" color="primary" />}
              {settings.saveHistory && <Chip label="Save history" size="small" color="primary" />}
              {settings.enableNotifications && <Chip label="Notifications" size="small" color="primary" />}
            </Box>
          </CardContent>
        </Card>
      </DialogContent>

      <DialogActions>
        <Button
          startIcon={<RestoreIcon />}
          onClick={handleReset}
          color="warning"
        >
          Reset to Defaults
        </Button>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSave} variant="contained">
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;
