import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import {
  Help as HelpIcon,
  Code as CodeIcon,
  CompareArrows as DiffIcon,
  AutoAwesome as AIIcon,
  Speed as SpeedIcon,
  BugReport as BugIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface HelpDialogProps {
  open: boolean;
  onClose: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`help-tabpanel-${index}`}
    aria-labelledby={`help-tab-${index}`}
  >
    {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
  </div>
);

const SAMPLE_GIT_DIFF = `diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -10,7 +10,10 @@ def calculate_total(items):
     total = 0
     for item in items:
-        total += item.price
+        if item.price is not None:
+            total += item.price
+        else:
+            print(f"Warning: Item {item.name} has no price")
     return total`;

const CRITERIA_LIST = [
  { name: 'Code Quality', description: 'Overall structure, naming, and organization' },
  { name: 'Security', description: 'Vulnerabilities and security best practices' },
  { name: 'Performance', description: 'Efficiency and optimization opportunities' },
  { name: 'Maintainability', description: 'Ease of maintenance and modification' },
  { name: 'Readability', description: 'Code clarity and documentation' },
  { name: 'Testing', description: 'Test coverage and quality' },
  { name: 'Error Handling', description: 'Exception handling and edge cases' },
  { name: 'Documentation', description: 'Comments and API documentation' },
  { name: 'Best Practices', description: 'Language-specific conventions' },
  { name: 'Architecture', description: 'Design patterns and structure' },
  { name: 'Scalability', description: 'Ability to handle growth' },
  { name: 'Resource Usage', description: 'Memory and CPU efficiency' },
  { name: 'Compatibility', description: 'Cross-platform and version compatibility' },
  { name: 'Dependencies', description: 'Third-party library usage' },
  { name: 'Configuration', description: 'Settings and environment handling' },
  { name: 'Logging', description: 'Debugging and monitoring capabilities' },
];

const HelpDialog: React.FC<HelpDialogProps> = ({ open, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HelpIcon />
          Help & Documentation
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="Getting Started" />
            <Tab label="Git Diff Format" />
            <Tab label="Analysis Criteria" />
            <Tab label="Tips & Tricks" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" gutterBottom>
            Welcome to AI Code Review Assistant
          </Typography>
          <Typography paragraph>
            This tool uses advanced AI to analyze your code changes and provide comprehensive feedback
            across 16 different quality criteria. Here's how to get started:
          </Typography>

          <List>
            <ListItem>
              <ListItemIcon>
                <CheckIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="1. Paste Your Code"
                secondary="Copy and paste your git diff or raw code into the left panel"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="2. Click Analyze"
                secondary="Our AI will analyze your code across multiple quality dimensions"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="3. Review Results"
                secondary="Get detailed feedback, suggestions, and actionable recommendations"
              />
            </ListItem>
          </List>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Pro Tip</Typography>
            For best results, use git diff format which provides context about what changed.
            The tool also works with raw code snippets.
          </Alert>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Typography variant="h6" gutterBottom>
            Git Diff Format Guide
          </Typography>
          <Typography paragraph>
            Git diff format shows changes between versions of files. Here's what each part means:
          </Typography>

          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Sample Git Diff:
              </Typography>
              <SyntaxHighlighter
                language="diff"
                style={oneLight}
                customStyle={{ fontSize: '12px' }}
              >
                {SAMPLE_GIT_DIFF}
              </SyntaxHighlighter>
            </CardContent>
          </Card>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Understanding Git Diff Syntax</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="diff --git a/file b/file"
                    secondary="Shows which file is being compared"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="--- a/file (old version)"
                    secondary="Lines starting with --- show the original file"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="+++ b/file (new version)"
                    secondary="Lines starting with +++ show the new file"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="@@ -10,7 +10,10 @@"
                    secondary="Shows line numbers: old file (start,count) new file (start,count)"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="- removed line"
                    secondary="Lines starting with - were removed"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="+ added line"
                    secondary="Lines starting with + were added"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="  context line"
                    secondary="Lines with no prefix provide context"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>

          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              How to Generate Git Diffs:
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace' }}>
                  {`# Compare working directory to last commit
git diff

# Compare specific commits
git diff commit1 commit2

# Compare specific file
git diff HEAD -- filename

# Get diff of staged changes
git diff --cached`}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" gutterBottom>
            Analysis Criteria (16 Categories)
          </Typography>
          <Typography paragraph>
            Our AI evaluates your code across these comprehensive criteria:
          </Typography>

          <Box sx={{ display: 'grid', gap: 2 }}>
            {CRITERIA_LIST.map((criteria, index) => (
              <Card key={index} variant="outlined">
                <CardContent sx={{ pb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      size="small"
                      label={`${index + 1}`}
                      color="primary"
                      variant="outlined"
                    />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {criteria.name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {criteria.description}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>

          <Alert severity="success" sx={{ mt: 3 }}>
            <Typography variant="subtitle2">Scoring System</Typography>
            Each criterion is scored from 0-10, with detailed feedback and actionable suggestions
            provided for improvement areas.
          </Alert>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Typography variant="h6" gutterBottom>
            Tips for Better Analysis
          </Typography>

          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Input Best Practices</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <DiffIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Use Git Diff Format"
                    secondary="Provides context about what changed, leading to more accurate analysis"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CodeIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Include Context Lines"
                    secondary="More context helps the AI understand the full picture"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Specify Language"
                    secondary="While auto-detected, specifying helps with language-specific analysis"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Interpreting Results</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Overall Score (8-10)"
                    secondary="Excellent code quality with minor suggestions"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon color="info" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Overall Score (6-7)"
                    secondary="Good code with some areas for improvement"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Overall Score (4-5)"
                    secondary="Needs attention in several areas"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon color="error" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Overall Score (0-3)"
                    secondary="Significant issues that should be addressed"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Advanced Features</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <LightbulbIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Sample Diffs"
                    secondary="Use the sample diffs in the input panel to see how analysis works"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <BugIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Export Results"
                    secondary="Download analysis results as JSON for sharing or record keeping"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AIIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Responsive Design"
                    secondary="Works great on desktop and mobile devices"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default HelpDialog;
