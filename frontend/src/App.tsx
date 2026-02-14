import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import PreciousMetals from "./pages/PreciousMetals";
import Gold from "./pages/metals/Gold";
import Silver from "./pages/metals/Silver";
import Platinum from "./pages/metals/Platinum";
import Palladium from "./pages/metals/Palladium";
import Gemstones from "./pages/Gemstones";
import Diamonds from "./pages/gemstones/Diamonds";
import Rubies from "./pages/gemstones/Rubies";
import Sapphires from "./pages/gemstones/Sapphires";
import Emeralds from "./pages/gemstones/Emeralds";
import JewelryInvestment from "./pages/JewelryInvestment";
import MarketInsights from "./pages/MarketInsights";
import TopDealers from "./pages/TopDealers";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Article from "./pages/Article";
import EditorialStandards from "./pages/EditorialStandards";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import AffiliateDisclosure from "./pages/AffiliateDisclosure";
import Cookies from "./pages/Cookies";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/precious-metals" element={<PreciousMetals />} />
          <Route path="/precious-metals/gold" element={<Gold />} />
          <Route path="/precious-metals/silver" element={<Silver />} />
          <Route path="/precious-metals/platinum" element={<Platinum />} />
          <Route path="/precious-metals/palladium" element={<Palladium />} />
          <Route path="/gemstones" element={<Gemstones />} />
          <Route path="/gemstones/diamonds" element={<Diamonds />} />
          <Route path="/gemstones/rubies" element={<Rubies />} />
          <Route path="/gemstones/sapphires" element={<Sapphires />} />
          <Route path="/gemstones/emeralds" element={<Emeralds />} />
          <Route path="/jewelry-investment" element={<JewelryInvestment />} />
          <Route path="/market-insights" element={<MarketInsights />} />
          <Route path="/top-dealers" element={<TopDealers />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/articles/:slug" element={<Article />} />
          <Route path="/editorial-standards" element={<EditorialStandards />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/affiliate-disclosure" element={<AffiliateDisclosure />} />
          <Route path="/cookies" element={<Cookies />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
