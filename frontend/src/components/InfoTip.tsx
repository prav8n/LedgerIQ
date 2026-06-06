import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Tooltip } from '@mui/material';

interface Props {
  /** Explanation text. Use `\n` for line breaks (e.g. before an example). */
  text: string;
}

/** A small hoverable ⓘ icon that explains a field, ideally with an example. */
export function InfoTip({ text }: Props) {
  return (
    <Tooltip
      arrow
      enterTouchDelay={0}
      leaveTouchDelay={6000}
      title={<span style={{ whiteSpace: 'pre-line' }}>{text}</span>}
    >
      <InfoOutlinedIcon
        sx={{ fontSize: 16, color: 'text.disabled', cursor: 'help', flexShrink: 0 }}
      />
    </Tooltip>
  );
}
