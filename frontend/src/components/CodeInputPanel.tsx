import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Toolbar,
  Tooltip,
  Chip,
  Divider,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  PlayArrow as AnalyzeIcon,
  Clear as ClearIcon,
  ContentPaste as PasteIcon,
  FileUpload as UploadIcon,
  MoreVert as MoreIcon,
  Code as CodeIcon,
  CompareArrows as DiffIcon,
  FormatSize as FormatIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeInputPanelProps {
  value: string;
  onChange: (value: string) => void;
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onAnalyze: (code: string, prompt: string) => void;
  onClear: () => void;
  loading: boolean;
  error: string | null;
}

const SAMPLE_DIFFS = {
  'Simple Function Change': `diff --git a/src/utils.py b/src/utils.py
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
     return total`,
  
  'React Component Update': `diff --git a/components/UserProfile.tsx b/components/UserProfile.tsx
index 1234567..abcdefg 100644
--- a/components/UserProfile.tsx
+++ b/components/UserProfile.tsx
@@ -15,8 +15,12 @@ const UserProfile: React.FC<Props> = ({ user }) => {
   return (
     <div className="user-profile">
-      <h2>{user.name}</h2>
-      <p>{user.email}</p>
+      <h2>{user.name || 'Anonymous User'}</h2>
+      <p>{user.email || 'No email provided'}</p>
+      {user.avatar && (
+        <img src={user.avatar} alt="User avatar" />
+      )}
+      <div>Last seen: {user.lastSeen || 'Never'}</div>
     </div>
   );
 };`,

  'Database Query Optimization': `diff --git a/database/queries.sql b/database/queries.sql
index 1234567..abcdefg 100644
--- a/database/queries.sql
+++ b/database/queries.sql
@@ -5,10 +5,12 @@
 -- Get user orders with product details
-SELECT u.name, o.order_date, p.product_name, oi.quantity
+SELECT u.name, o.order_date, p.product_name, oi.quantity, p.category
 FROM users u
-JOIN orders o ON u.id = o.user_id
-JOIN order_items oi ON o.id = oi.order_id
-JOIN products p ON oi.product_id = p.id
-ORDER BY o.order_date DESC;
+  INNER JOIN orders o ON u.id = o.user_id
+  INNER JOIN order_items oi ON o.id = oi.order_id
+  INNER JOIN products p ON oi.product_id = p.id
+WHERE o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
+  AND u.status = 'active'
+ORDER BY o.order_date DESC
+LIMIT 100;`
};

const CodeInputPanel: React.FC<CodeInputPanelProps> = ({
  value,
  onChange,
  prompt,
  onPromptChange,
  onAnalyze,
  onClear,
  loading,
  error,
}) => {
  const [inputMode, setInputMode] = useState<'text' | 'preview'>('text');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePaste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      onChange(text);
    } catch (err) {
      console.error('Failed to paste from clipboard:', err);
    }
  }, [onChange]);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        onChange(content);
      };
      reader.readAsText(file);
    }
  }, [onChange]);

  const handleSampleSelect = useCallback((sample: string) => {
    onChange(SAMPLE_DIFFS[sample as keyof typeof SAMPLE_DIFFS]);
    setMenuAnchor(null);
  }, [onChange]);

  const detectFormat = useCallback((text: string) => {
    if (text.includes('diff --git') || text.includes('@@') || text.includes('+++') || text.includes('---')) {
      return 'git-diff';
    }
    return 'code';
  }, []);

  const format = detectFormat(value);
  const lineCount = value.split('\n').length;
  const charCount = value.length;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Toolbar variant="dense" sx={{ minHeight: 48 }}>
        <Typography variant="h6" sx={{ flexGrow: 1, fontSize: '1rem' }}>
          Code Input
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            size="small"
            label={format === 'git-diff' ? 'Git Diff' : 'Raw Code'}
            color={format === 'git-diff' ? 'primary' : 'default'}
            icon={format === 'git-diff' ? <DiffIcon /> : <CodeIcon />}
          />
          
          <Tooltip title="Toggle preview">
            <IconButton
              size="small"
              onClick={() => setInputMode(inputMode === 'text' ? 'preview' : 'text')}
              color={inputMode === 'preview' ? 'primary' : 'default'}
            >
              <FormatIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Paste from clipboard">
            <IconButton size="small" onClick={handlePaste}>
              <PasteIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Upload file">
            <IconButton size="small" onClick={() => fileInputRef.current?.click()}>
              <UploadIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="More options">
            <IconButton
              size="small"
              onClick={(e) => setMenuAnchor(e.currentTarget)}
            >
              <MoreIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
      
      <Divider />

      {/* Content - Split into Code and Prompt sections */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Code Input Section */}
        <Box sx={{ flex: 1, p: 2, minHeight: 0 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Code Input
          </Typography>
          {inputMode === 'text' ? (
            <TextField
              multiline
              fullWidth
              placeholder="Paste your git diff or code here for AI analysis..."
              value={value}
              onChange={(e) => onChange(e.target.value)}
              sx={{
                height: 'calc(100% - 24px)',
                '& .MuiInputBase-root': {
                  height: '100%',
                  alignItems: 'flex-start',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                  fontSize: '14px',
                  lineHeight: 1.5,
                },
                '& .MuiInputBase-input': {
                  height: '100% !important',
                  overflow: 'auto !important',
                  resize: 'none',
                },
                '& .MuiOutlinedInput-root': {
                  height: '100%',
                }
              }}
              minRows={10}
              maxRows={25}
            />
        ) : (
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            {value ? (
              <SyntaxHighlighter
                language={format === 'git-diff' ? 'diff' : 'javascript'}
                style={oneLight}
                customStyle={{
                  margin: 0,
                  height: '100%',
                  fontSize: '14px',
                  lineHeight: 1.5,
                }}
              >
                {value}
              </SyntaxHighlighter>
            ) : (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  fontStyle: 'italic',
                  textAlign: 'center',
                  mt: 4,
                }}
              >
                Code preview will appear here...
              </Typography>
            )}
          </Box>
        )}
        </Box>
        
        <Divider />
        
        {/* AI Prompt Section */}
        <Box sx={{ flex: 0.6, p: 2, minHeight: 0 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            AI Analysis Prompt
          </Typography>
          <TextField
            multiline
            fullWidth
            placeholder="Customize the AI analysis prompt..."
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            sx={{
              height: 'calc(100% - 24px)',
              '& .MuiInputBase-root': {
                height: '100%',
                alignItems: 'flex-start',
                fontSize: '14px',
                lineHeight: 1.5,
              },
              '& .MuiInputBase-input': {
                height: '100% !important',
                overflow: 'auto !important',
                resize: 'none',
              },
              '& .MuiOutlinedInput-root': {
                height: '100%',
              }
            }}
            minRows={6}
          />
        </Box>
      </Box>

      {/* Footer */}
      <Divider />
      <Box sx={{ p: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {lineCount} lines, {charCount} characters
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={onClear}
              disabled={loading || !value}
            >
              Clear
            </Button>
            <Button
              variant="contained"
              startIcon={<AnalyzeIcon />}
              onClick={() => onAnalyze(value, prompt)}
              disabled={loading || !value.trim()}
            >
              {loading ? 'Analyzing...' : 'Analyze Code'}
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept=".txt,.diff,.patch,.js,.ts,.py,.java,.cpp,.c,.h,.css,.html,.json,.xml,.yml,.yaml"
        style={{ display: 'none' }}
      />

      {/* Sample menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <ListItemText primary="Load Sample Diffs" secondary="Choose from examples" />
        </MenuItem>
        <Divider />
        {Object.keys(SAMPLE_DIFFS).map((sampleName) => (
          <MenuItem key={sampleName} onClick={() => handleSampleSelect(sampleName)}>
            <ListItemIcon>
              <DiffIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary={sampleName} />
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default CodeInputPanel;
