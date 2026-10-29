import type { Metadata } from "next";
import { AuthProvider } from "@/components/auth-provider";
import { AppHeader } from "@/components/app-header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Akasha — votre avenir professionnel",
  description:
    "Découvrez des opportunités, valorisez vos compétences et faites avancer votre parcours professionnel avec Akasha.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr">
      <body className="min-h-screen flex flex-col">
        <AuthProvider>
          <AppHeader />
          {children}
          <footer className="footer">
            <div className="footer-inner">
              <span>© Akasha — les compétences ouvrent des possibles.</span>
              <span>Découvrez des opportunités, valorisez votre profil et suivez votre parcours.</span>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
