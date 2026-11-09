import React from "react";
import {getInputProps} from "remotion";
import {ShortPlayer} from "../../engine";
import {World} from "./world";
import {TOTAL, SHOTS, cameraAt, engineDofAt} from "./story";
export const ELEVATOR_CRUSH_FRAMES = TOTAL;
export const HUD: Record<number, string> = {
  1: "😱 TRAPPED WITH CRUSH • 03:00:00",
  2: "🌧️ 1 SEC BEFORE CLOSING!",
  3: "⚡ POWER CUT • STUCK AT FLOOR 4!",
  4: "📵 HOUR 1 • ZERO NETWORK",
  5: "💀 ACTING NATURAL: 0%",
  6: "😭 STOMACH GROWLED IN SILENCE!",
  7: "⚠️ HOUR 2 • CABLE SLIPS 2 FEET!",
  8: "❤️ HEART RATE: 160 BPM!",
  9: "🔥 'जब तक मैं हूँ, तुम्हें कुछ नहीं होगा'",
  10: "✨ AWKWARDNESS: 0% • EYE CONTACT",
  11: "👇 COMMENT 'PART 2' NOW! 🔥",
};
export const CUES: [number, number, string][] = [
  [0, 104, "सोचो अगर शाम की कोचिंग के बाद,"],
  [105, 209, "तुम और तुम्हारी क्रश 3 घंटों के लिए लिफ्ट में फँस जाओ!"],
  [210, 305, "बाहर तेज़ बारिश है, तुम लिफ्ट में अकेले हो..."],
  [306, 404, "और दरवाज़ा बंद होने से 1 सेकंड पहले वो अंदर आती है!"],
  [405, 485, "अभी तुम अपनी धड़कनें संभाल ही रहे होते हो"],
  [486, 570, "कि अचानक—भड़ाम! पूरी बिल्डिंग की लाइट कट जाती है,"],
  [571, 659, "और लिफ्ट चौथे फ्लोर के बीचों-बीच अटक जाती है!"],
  [660, 775, "पहला घंटा... भाई, एकदम जानलेवा ऑकवर्डनेस!"],
  [776, 905, "पिन-ड्रॉप साइलेंस है, और फ़ोन में नेटवर्क ज़ीरो।"],
  [906, 1030, "वो एक कोने में खड़ी अपने बाल ठीक कर रही है,"],
  [1031, 1169, "और तुम दूसरे कोने में फ्लोर बटन्स घूर रहे हो!"],
  [1170, 1310, "तुम कुछ बोलने के लिए मुँह खोलते हो, पर गला सूख जाता है।"],
  [1311, 1420, "ऊपर से खाली पेट में ज़ोर से गुड़गुड़ होती है—"],
  [1421, 1523, "लगता है धरती फट जाए और तुम समा जाओ!"],
  [1524, 1664, "तभी दूसरा घंटा... और केबल से आवाज़ आती है—खड़-खड़-खड़!"],
  [1665, 1817, "लिफ्ट 2 फीट नीचे खिसकती है और इमरजेंसी लाइट भी बंद!"],
  [1818, 1995, "डर से वो दौड़कर सीधा तुम्हारे सीने से लिपट जाती है!"],
  [1996, 2195, "तुम्हारे दिल की धड़कन सीधा उसके कानों में सुनाई देती है।"],
  [2196, 2330, "तुम काँपते हाथों से उसके कंधे को थामते हो—"],
  [2331, 2465, "'डरो मत, सेफ्टी ब्रेक्स लॉक हैं। तुम्हें कुछ नहीं होगा।'"],
  [2466, 2630, "5 सेकंड बाद डिम लाइट आती है, पर वो तुम्हें नहीं छोड़ती।"],
  [2631, 2834, "वो तुम्हारी आँखों में देखती है और ऑकवर्डनेस गायब!"],
  [2835, 3020, "पर असली खेल अब शुरू होता है—वो एक राज़ खोलने वाली है,"],
  [3021, 3205, "और तुम्हारी हथेली पर कुछ ऐसा लिखकर जाएगी कि होश उड़ जाएँगे!"],
  [3206, 3344, "आगे जानने के लिए अभी कमेंट करो 'PART 2' और फॉलो कर लो!"],
];


const createWorld=()=>new World();
const shots=SHOTS.map(s=>({...s,hud:HUD[s.id],grade:s.light==="rainy"||s.light==="violetRim"||s.light==="neon"?"twilight":"warm",exposure:1.0}));
export const ElevatorCrushShort:React.FC<{subs?:boolean}>=(props)=>{
 const input=getInputProps() as {subs?:boolean;post?:{dpr?:number}};
 return <ShortPlayer createWorld={createWorld} shots={shots} cues={CUES} camAt={cameraAt} dofAt={engineDofAt}
  audio="elevator_crush/audio.mp3" subs={props.subs??input.subs??true} dpr={input.post?.dpr} background="#6c626f"/>;
};
