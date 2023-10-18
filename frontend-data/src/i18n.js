import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./i18n/en/translation.json";

const resources = {
  returnNull: false,
  'en': {
    translation: en,
  },
  
};

i18n.use(initReactI18next).init({
  returnNull: false,
  resources, // 會是所有翻譯資源
  fallbackLng: "zh-hant", // 如果當前切換的語言沒有對應的翻譯則使用這個語言
  lng: "zh-hant", // 預設語言
  interpolation: { 
    escapeValue: false,// 是否要讓字詞 escaped 來防止 xss 攻擊，這裡因為 React.js 已經做了，就設成 false即可
  },
});

export default i18n;