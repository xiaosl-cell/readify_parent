/// <reference types="vite/client" />

// 声明Markmap全局类型
interface Window {
  d3: any;
  minimalD3: any;
  markmap: {
    Markmap: any;
    Transformer: any;
    loadCSS?: any;
    loadJS?: any;
  };
  Markmap?: any;
  Transformer?: any;
  minimalMarkmap: {
    Markmap: any;
    Transformer: any;
  }
}
