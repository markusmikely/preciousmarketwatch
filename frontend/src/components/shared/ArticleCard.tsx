import { Link } from "react-router-dom";
import { Clock, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface ArticleCardProps {
  title: string;
  excerpt: string;
  category: string;
  author: string;
  date: string;
  readTime: string;
  image: string;
  href: string;
  featured?: boolean;
}

export function ArticleCard({
  title,
  excerpt,
  category,
  author,
  date,
  readTime,
  image,
  href,
  featured = false,
}: ArticleCardProps) {
  if (featured) {
    return (
      <Link to={href} className="group block">
        <article className="relative h-[400px] lg:h-[500px] rounded-xl overflow-hidden">
          <img
            src={image}
            alt={title}
            className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-navy via-navy/60 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-6 lg:p-8">
            <Badge className="mb-3 bg-primary text-primary-foreground">{category}</Badge>
            <h3 className="font-display text-2xl lg:text-3xl font-bold text-silver-light mb-3 group-hover:text-primary transition-colors">
              {title}
            </h3>
            <p className="text-silver line-clamp-2 mb-4">{excerpt}</p>
            <div className="flex items-center gap-4 text-sm text-silver/80">
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" />
                {author}
              </span>
              <span>{date}</span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {readTime}
              </span>
            </div>
          </div>
        </article>
      </Link>
    );
  }

  return (
    <Link to={href} className="group block">
      <article className="h-full bg-card rounded-xl overflow-hidden border border-border hover:border-primary/50 hover:shadow-lg transition-all duration-300">
        <div className="aspect-[16/10] overflow-hidden">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        </div>
        <div className="p-5">
          <Badge variant="secondary" className="mb-3">
            {category}
          </Badge>
          <h3 className="font-display text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors line-clamp-2">
            {title}
          </h3>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{excerpt}</p>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{author}</span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {readTime}
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
