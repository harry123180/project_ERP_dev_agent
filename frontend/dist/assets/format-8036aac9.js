import{bp as f}from"./index-61294aba.js";const e=(r,t="NT$")=>{if(r==null||r==="")return`${t} 0`;const s=typeof r=="string"?parseFloat(r):r;return isNaN(s)?`${t} 0`:`${t} ${s.toLocaleString("zh-TW")}`},i=(r,t="YYYY-MM-DD HH:mm:ss")=>r?f(r).format(t):"-";export{i as a,e as f};
//# sourceMappingURL=format-8036aac9.js.map
