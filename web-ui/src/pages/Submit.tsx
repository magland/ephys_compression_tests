import submitContent from "./submit.md?raw";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export default function Submit() {
  return (
    <div className="content-container">
      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
        {submitContent}
      </ReactMarkdown>
    </div>
  );
}
