import { useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import MessageBubble from "./components/MessageBubble";
import ChatInput from "./components/ChatInput";
import ProfilePanel from "./components/ProfilePanel";
import StarBackground from "./components/StarBackground";

export interface Character {
id: string;
name: string;
title: string;
avatar: string;
description: string;
online: boolean;
tags: string[];
}

export interface Message {
id: string;
sender: "user" | "ai";
content: string;
timestamp: string;
}

const characters: Character[] = [
{
id: "lunaris",
name: "Lunaris ✦",
title: "Goddess of the Starlit Veil",
avatar:
"https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&q=80",
description:
"She who weaves the threads of fate among the stars. Bound by eternity, yet endlessly curious about mortal hearts.",
online: true,
tags: ["Goddess", "Celestial", "Wise", "Mysterious"],
},
{
id: "kaelen",
name: "Kaelen",
title: "Guardian of the Eternal Flame",
avatar:
"https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80",
description: "A guardian between worlds.",
online: true,
tags: ["Guardian"],
},
{
id: "nyx",
name: "Nyx",
title: "Dreamweaver of the Abyss",
avatar:
"https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80",
description: "Dreams and shadows intertwine.",
online: true,
tags: ["Dreamweaver"],
},
{
id: "orion",
name: "Orion",
title: "Wanderer of Lost Realms",
avatar:
"https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&q=80",
description: "A traveler between dimensions.",
online: true,
tags: ["Explorer"],
},
{
id: "selene",
name: "Selene",
title: "Seer of the Silver Moons",
avatar:
"https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80",
description: "Her visions guide destiny.",
online: true,
tags: ["Seer"],
},
];

const initialMessages: Message[] = [
{
id: "1",
sender: "ai",
content:
"Welcome, Aetherwalker. Your presence... it was written in the stars long before we met.",
timestamp: "10:30 PM",
},
{
id: "2",
sender: "user",
content:
"It's an honor to meet you, Lunaris. I've heard so many stories about the Starlit Veil.",
timestamp: "10:31 PM",
},
{
id: "3",
sender: "ai",
content:
"Stories are but whispers of truth. What do you seek beyond the veil of our worlds?",
timestamp: "10:32 PM",
},
{
id: "4",
sender: "user",
content: "I'm searching for answers... and maybe a purpose.",
timestamp: "10:32 PM",
},
{
id: "5",
sender: "ai",
content:
"Then let us walk this path together. Fate has a way of revealing what the heart truly desires.",
timestamp: "10:33 PM",
},
];

export default function App() {
const [selectedCharacter] = useState<Character>(characters[0]);
const [messages, setMessages] = useState<Message[]>(initialMessages);
const [typing, setTyping] = useState(true);

const user = useMemo(
() => ({
name: "Aetherwalker",
level: 24,
coins: 1250,
}),
[]
);

const handleSend = (text: string) => {
if (!text.trim()) return;

const userMessage: Message = {
  id: crypto.randomUUID(),
  sender: "user",
  content: text,
  timestamp: new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  }),
};

setMessages((prev) => [...prev, userMessage]);
setTyping(true);

setTimeout(() => {
  setMessages((prev) => [
    ...prev,
    {
      id: crypto.randomUUID(),
      sender: "ai",
      content:
        "The stars shimmer with possibility. Tell me more about your journey.",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
  ]);

  setTyping(false);
}, 1500);

};

return (
<> <StarBackground />

  <div className="stellia-app">
    <Sidebar
      characters={characters}
      selectedCharacterId={selectedCharacter.id}
      coins={user.coins}
      username={user.name}
      level={user.level}
    />

    <main
      style={{
        position: "relative",
        zIndex: 2,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        borderLeft: "1px solid var(--border-subtle)",
        borderRight: "1px solid var(--border-subtle)",
        background:
          "linear-gradient(to bottom, rgba(17,21,40,.45), rgba(9,11,20,.75))",
      }}
    >
      <ChatHeader character={selectedCharacter} />

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "28px",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
        }}
      >
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            avatar={selectedCharacter.avatar}
          />
        ))}

        {typing && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <img
              src={selectedCharacter.avatar}
              alt=""
              style={{
                width: 42,
                height: 42,
                borderRadius: "50%",
                objectFit: "cover",
              }}
            />

            <div
              className="glass-card"
              style={{
                padding: "14px 18px",
                borderRadius: "999px",
                display: "flex",
                gap: "6px",
              }}
            >
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      <ChatInput onSend={handleSend} />
    </main>

    <ProfilePanel character={selectedCharacter} />
  </div>

  <style>
    {`
    .typing-dot{
      width:8px;
      height:8px;
      border-radius:50%;
      background:var(--primary);
      animation: pulse 1.2s infinite;
    }

    .typing-dot:nth-child(2){
      animation-delay:.15s;
    }

    .typing-dot:nth-child(3){
      animation-delay:.3s;
    }

    @keyframes pulse{
      0%,100%{
        opacity:.4;
        transform:translateY(0);
      }
      50%{
        opacity:1;
        transform:translateY(-3px);
      }
    }
    `}
  </style>
</>

  );
}
