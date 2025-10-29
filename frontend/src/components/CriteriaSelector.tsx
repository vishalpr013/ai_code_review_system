import React, { useState } from 'react';
import {
  Box,
  Typography,
  FormGroup,
  FormControlLabel,
  Switch,
  Paper,
  Divider,
  Chip,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Code as CodeIcon,
  Security as SecurityIcon,
  FormatAlignLeft as FormatIcon,
  BugReport as BugIcon,
  Architecture as ArchitectureIcon,
  Comment as CommentIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

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

interface CriteriaSelectorProps {
  config: CriteriaConfig;
  onToggle: (key: keyof CriteriaConfig) => void;
}

const criteriaGroups = {
  'Code Quality': {
    icon: <CodeIcon />,
    color: '#1976d2',
    items: [
      { key: 'areCodeChangesOptimized', label: 'Code Changes Optimized' },
      { key: 'isCodeWellWritten', label: 'Code Well Written' },
      { key: 'isCodeFormatted', label: 'Code Formatted' },
      { key: 'isNamingConventionFollowed', label: 'Naming Convention' },
    ]
  },
  'Documentation': {
    icon: <CommentIcon />,
    color: '#388e3c',
    items: [
      { key: 'areCommentsWritten', label: 'Comments Written' },
      { key: 'isCommitMessageWellWritten', label: 'Commit Message Quality' },
      { key: 'areThereAnySpellingMistakes', label: 'Check Spelling' },
    ]
  },
  'Security & Bugs': {
    icon: <SecurityIcon />,
    color: '#d32f2f',
    items: [
      { key: 'securityConcernsAny', label: 'Security Concerns' },
      { key: 'loopholes', label: 'Loopholes Detection' },
      { key: 'missingElements', label: 'Missing Elements' },
    ]
  },
  'Architecture': {
    icon: <ArchitectureIcon />,
    color: '#7b1fa2',
    items: [
      { key: 'isCodeModular', label: 'Code Modularity' },
      { key: 'areConstantsDefinedCentrally', label: 'Constants Management' },
      { key: 'isLoggingDoneProperly', label: 'Logging Implementation' },
      { key: 'isCodeDuplicated', label: 'Code Duplication Check' },
    ]
  },
  'Complexity': {
    icon: <BugIcon />,
    color: '#f57c00',
    items: [
      { key: 'cyclomaticComplexityScore', label: 'Cyclomatic Complexity' },
      { key: 'areCodeChangesRelative', label: 'Changes Relative to Context' },
    ]
  }
};

const CriteriaSelector: React.FC<CriteriaSelectorProps> = ({ config, onToggle }) => {
  const enabledCount = Object.values(config).filter(Boolean).length;
  const totalCount = Object.keys(config).length;
  const [expanded, setExpanded] = useState(false);

  return (
    <Paper sx={{ mb: 2 }}>
      {/* Header - Always Visible */}
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          cursor: 'pointer'
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" component="div">
            Analysis Criteria
          </Typography>
          <Chip 
            label={`${enabledCount}/${totalCount} enabled`} 
            color="primary" 
            variant="outlined" 
            size="small"
          />
        </Box>
        
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      
      {/* Collapsible Content */}
      <Collapse in={expanded}>
        <Box sx={{ px: 2, pb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select which criteria you want the AI to evaluate in your code review.
          </Typography>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr', lg: '1fr 1fr 1fr' },
        gap: 3 
      }}>
        {Object.entries(criteriaGroups).map(([groupName, group]) => (
          <Box key={groupName} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box sx={{ color: group.color, mr: 1 }}>
                {group.icon}
              </Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: group.color }}>
                {groupName}
              </Typography>
            </Box>
            
            <FormGroup>
              {group.items.map(({ key, label }) => (
                <FormControlLabel
                  key={key}
                  control={
                    <Switch
                      checked={config[key as keyof CriteriaConfig]}
                      onChange={() => onToggle(key as keyof CriteriaConfig)}
                      size="small"
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: group.color,
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: group.color,
                        },
                      }}
                    />
                  }
                  label={
                    <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                      {label}
                    </Typography>
                  }
                  sx={{ ml: 0, mb: 0.5 }}
                />
              ))}
            </FormGroup>
          </Box>
        ))}
      </Box>

      <Divider sx={{ my: 2 }} />
      
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="caption" color="text.secondary">
          Quick actions:
        </Typography>
        <Chip
          label="Enable All"
          size="small"
          variant="outlined"
          onClick={() => {
            // Create new config with all true
            const allEnabled = Object.keys(config).reduce((acc, key) => ({
              ...acc,
              [key]: true
            }), {} as CriteriaConfig);
            
            // Toggle only the ones that are currently false
            Object.keys(config).forEach(key => {
              if (!config[key as keyof CriteriaConfig]) {
                onToggle(key as keyof CriteriaConfig);
              }
            });
          }}
          sx={{ fontSize: '0.75rem' }}
        />
        <Chip
          label="Disable All"
          size="small"
          variant="outlined"
          onClick={() => {
            Object.keys(config).forEach(key => {
              if (config[key as keyof CriteriaConfig]) {
                onToggle(key as keyof CriteriaConfig);
              }
            });
          }}
          sx={{ fontSize: '0.75rem' }}
        />
        <Chip
          label="Quality Only"
          size="small"
          variant="outlined"
          onClick={() => {
            // First disable all
            Object.keys(config).forEach(key => {
              if (config[key as keyof CriteriaConfig]) {
                onToggle(key as keyof CriteriaConfig);
              }
            });
            // Then enable quality criteria
            const qualityCriteria: (keyof CriteriaConfig)[] = [
              'areCodeChangesOptimized', 
              'isCodeWellWritten', 
              'isCodeFormatted', 
              'isNamingConventionFollowed'
            ];
            setTimeout(() => {
              qualityCriteria.forEach(key => {
                if (!config[key]) {
                  onToggle(key);
                }
              });
            }, 100);
          }}
          sx={{ fontSize: '0.75rem' }}
        />
      </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default CriteriaSelector;
