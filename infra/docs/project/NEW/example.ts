import React, { useState } from 'react';
import {
  Camera,
  ShoppingCart,
  Globe,
  ShoppingBag,
  ArrowLeft,
  ArrowRight,
  Instagram,
  Facebook,
  Mail,
  Search,
  ChevronDown
} from 'lucide-react';

// --- Types ---
interface Product {
  id: number;
  title: string;
  category: string;
  series: string;
  price: number;
  image: string;
  badge?: string;
  description: string;
}

// --- Mock Data ---
const PRODUCTS: Product[] = [
  {
    id: 1,
    title: "The Great Orion Nebula",
    category: "Deep Sky",
    series: "Deep Sky Series",
    price: 85,
    image: "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=80&w=800",
    badge: "Bestseller",
    description: "Museum-grade archival print on Hahnemühle paper. Hand-signed by the artist."
  },
  {
    id: 2,
    title: "Galactic Core Over Alps",
    category: "Landscape",
    series: "Landscape Series",
    price: 120,
    image: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=800",
    badge: "New Release",
    description: "High-contrast panorama printed on premium gallery-wrap canvas."
  },
  {
    id: 3,
    title: "Andromeda Galaxy M31",
    category: "Deep Sky",
    series: "Deep Sky Series",
    price: 95,
    image: "https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&q=80&w=800",
    description: "Capturing 2.5 million light-years of detail in stunning resolution."
  },
  {
    id: 4,
    title: "The Diamond Ring",
    category: "Solar System",
    series: "Solar System",
    price: 110,
    image: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&q=80&w=800",
    description: "A rare moment of totality. Limited edition series of 50 prints."
  },
  {
    id: 5,
    title: "Emerald Night Veil",
    category: "Aurora",
    series: "Aurora Series",
    price: 75,
    image: "https://images.unsplash.com/photo-1537062225301-4b99e52943c0?auto=format&fit=crop&q=80&w=800",
    description: "The dancing spirits of the north captured in Lofoten, Norway."
  },
  {
    id: 6,
    title: "The Stargazer Guide",
    category: "Education",
    series: "Books & Media",
    price: 35,
    image: "https://images.unsplash.com/photo-1506318137071-a8e063b4bcc0?auto=format&fit=crop&q=80&w=800",
    badge: "Education",
    description: "Hardcover guide to finding and photographing the wonders of the night sky."
  }
];

const CATEGORIES = ["All Items", "Fine Art Prints", "Canvas", "Digital"];

// --- Components ---

const Navbar = () => (
  <nav className="flex items-center justify-between px-8 py-6 border-b border-white/5 sticky top-0 z-50 bg-[#0b0e14]/90 backdrop-blur-xl">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full border border-white/20 flex items-center justify-center overflow-hidden bg-black/50">
        <Camera className="w-5 h-5 text-blue-400" />
      </div>
      <div>
        <h1 className="text-sm font-bold tracking-widest uppercase text-white">Portfolio Owner</h1>
        <p className="text-[10px] text-blue-400 tracking-[0.2em] uppercase">Astrophotography</p>
      </div>
    </div>

    <div className="hidden md:flex items-center gap-8 text-[11px] font-semibold tracking-widest uppercase text-gray-400">
      <a href="#" className="hover:text-white transition-colors">Home</a>
      <a href="#" className="hover:text-white transition-colors">Astrophotography</a>
      <a href="#" className="text-white border-b border-blue-400 pb-1">Shop</a>
      <a href="#" className="hover:text-white transition-colors">About</a>
      <a href="#" className="hover:text-white transition-colors">Contact</a>
    </div>

    <div className="flex items-center gap-4 text-white">
      <div className="flex items-center gap-1 text-[10px] font-bold border border-white/10 px-3 py-1 rounded-full bg-white/5">
        <Globe className="w-3 h-3" />
        <span>EN</span>
        <span className="text-gray-600">|</span>
        <span className="text-gray-500">PL</span>
      </div>
      <button className="relative p-2 hover:bg-white/10 rounded-full transition-colors">
        <ShoppingCart className="w-5 h-5" />
        <span className="absolute top-0 right-0 w-4 h-4 bg-blue-500 text-[10px] rounded-full flex items-center justify-center font-bold">2</span>
      </button>
    </div>
  </nav>
);

const ProductCard = ({ product }: { product: Product }) => (
  <div className="bg-black/40 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden group transition-all duration-500 hover:border-blue-400/40 hover:-translate-y-2 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
    <div className="relative aspect-[4/5] overflow-hidden">
      <img
        src={product.image}
        alt={product.title}
        className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
      />
      {product.badge && (
        <div className="absolute top-5 left-5 z-10">
          <span className={`text-[10px] font-black uppercase px-4 py-1.5 rounded-full shadow-2xl text-white ${
            product.badge === 'Bestseller' ? 'bg-blue-600/90' :
            product.badge === 'New Release' ? 'bg-purple-600/90' : 'bg-amber-600/90'
          }`}>
            {product.badge}
          </span>
        </div>
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-20">
        <button className="bg-white text-black text-[10px] font-black uppercase px-8 py-4 rounded-full tracking-widest transform translate-y-4 group-hover:translate-y-0 transition-transform hover:bg-blue-400 transition-colors">
          Quick View
        </button>
      </div>
    </div>
    <div className="p-8 relative z-10">
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-[10px] text-blue-400 font-bold uppercase tracking-[0.2em] mb-2">{product.series}</p>
          <h3 className="text-xl font-bold text-white group-hover:text-blue-200 transition-colors">{product.title}</h3>
        </div>
        <div className="text-right">
          <p className="text-2xl font-light text-blue-300">${product.price}</p>
        </div>
      </div>
      <p className="text-sm text-gray-400 mb-8 leading-relaxed line-clamp-2">
        {product.description}
      </p>
      <button className="w-full bg-blue-400 hover:bg-blue-300 text-[#0b0e14] py-4 rounded-xl flex items-center justify-center gap-3 text-[11px] font-black uppercase tracking-[0.2em] shadow-lg transition-all active:scale-95">
        <ShoppingBag className="w-4 h-4" />
        Add to Cart
      </button>
    </div>
  </div>
);

export default function App() {
  const [activeCategory, setActiveCategory] = useState("All Items");

  return (
    <div className="min-h-screen bg-[#0b0e14] text-white relative font-['Inter']">

      {/* CORE COSMIC BACKGROUND
          - Fixed position
          - High resolution nebula
          - Gradient overlays for readability
      */}
      <div className="fixed inset-0 z-0">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=100&w=2500')`,
          }}
        />
        {/* Dark Vignette Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#0b0e14]/90 via-[#0b0e14]/60 to-[#0b0e14]" />
        {/* Subtle Grain Texture */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
      </div>

      <div className="relative z-10">
        <Navbar />

        <header className="pt-32 pb-20 text-center px-4 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-blue-400/30 bg-blue-400/10 text-blue-300 text-[10px] font-black uppercase tracking-[0.3em] mb-8 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            Documenting the Cosmos
          </div>
          <h2 className="text-5xl md:text-8xl font-bold tracking-tight mb-8 leading-tight">
            The Shop of <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-200 to-gray-500">Ancient Light.</span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed font-light">
            Each print is a window into the deep history of our universe.
            Archival quality materials ensuring the cosmos stays vibrant forever.
          </p>
        </header>

        <main className="max-w-7xl mx-auto px-8 pb-32">

          {/* Enhanced Filter Bar */}
          <div className="flex flex-col md:flex-row justify-between items-center gap-8 mb-16 border-b border-white/10 pb-10">
            <div className="flex flex-wrap justify-center gap-4">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-10 py-3 rounded-full text-[11px] font-black uppercase tracking-widest transition-all duration-300 ${
                    activeCategory === cat
                      ? "bg-blue-500 text-white shadow-[0_0_30px_rgba(59,130,246,0.3)] scale-105"
                      : "bg-white/5 border border-white/10 text-gray-400 hover:border-blue-400/50 hover:text-white"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-6">
               <div className="flex items-center gap-3 text-[11px] font-black uppercase tracking-widest text-gray-500 group cursor-pointer hover:text-white transition-colors">
                <span>Filter By</span>
                <ChevronDown className="w-4 h-4 text-blue-400" />
              </div>
              <div className="w-px h-6 bg-white/10" />
              <button className="text-gray-400 hover:text-blue-400 transition-colors">
                <Search className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Product Grid */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {PRODUCTS.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </section>

          {/* Pagination */}
          <div className="mt-32 flex justify-center items-center gap-8">
            <button className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 hover:text-blue-400 hover:border-blue-400/30 transition-all">
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="flex gap-3">
              {[1, 2, 3].map(num => (
                <button
                  key={num}
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center text-sm font-black transition-all ${
                    num === 1
                    ? "bg-blue-500 text-white shadow-[0_10px_20px_rgba(59,130,246,0.2)]"
                    : "bg-white/5 border border-white/10 text-gray-500 hover:text-white hover:bg-white/10"
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
            <button className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 hover:text-blue-400 hover:border-blue-400/30 transition-all">
              <ArrowRight className="w-6 h-6" />
            </button>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/10 py-20 bg-black/60 backdrop-blur-2xl">
          <div className="max-w-7xl mx-auto px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-16 mb-20">
              <div className="col-span-1 md:col-span-2">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 rounded-full border border-blue-400/30 flex items-center justify-center bg-blue-400/5">
                    <Camera className="w-6 h-6 text-blue-400" />
                  </div>
                  <h1 className="text-lg font-bold tracking-widest uppercase">Portfolio Owner</h1>
                </div>
                <p className="text-gray-500 max-w-sm leading-relaxed text-sm">
                  Documenting the vastness of space through specialized equipment and artistic interpretation. Every purchase supports the continued exploration of the night sky.
                </p>
              </div>
              <div>
                <h4 className="text-[11px] font-black uppercase tracking-[0.3em] text-blue-400 mb-8">Navigation</h4>
                <ul className="text-[11px] font-bold tracking-widest text-gray-400 space-y-5 uppercase">
                  <li><a href="#" className="hover:text-white transition-colors">Shipping</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Refunds</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-[11px] font-black uppercase tracking-[0.3em] text-blue-400 mb-8">Socials</h4>
                <div className="flex gap-5">
                  { [Instagram, Facebook, Mail].map((Icon, idx) => (
                    <a key={idx} href="#" className="w-12 h-12 flex items-center justify-center rounded-2xl bg-white/5 border border-white/10 text-gray-400 hover:text-blue-400 hover:border-blue-400/50 transition-all">
                      <Icon className="w-5 h-5" />
                    </a>
                  ))}
                </div>
              </div>
            </div>
            <div className="pt-10 border-t border-white/5 text-[10px] text-center text-gray-600 font-bold uppercase tracking-[0.4em]">
              &copy; 2024 Portfolio Owner Astrophotography
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
