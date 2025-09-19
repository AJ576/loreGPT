import { Cinzel, Uncial_Antiqua } from "next/font/google";
import "./globals.css";

const cinzel = Cinzel({
  variable: "--font-cinzel",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const uncialAntiqua = Uncial_Antiqua({
  variable: "--font-uncial",
  subsets: ["latin"],
  weight: ["400"],
});

export const metadata = {
  title: "CosmereArchivist - Archive of the Shards",
  description: "Seek knowledge from the ancient archives of the Cosmere",
  icons: {
    icon: "/coppermind.png",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${cinzel.variable} ${uncialAntiqua.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
