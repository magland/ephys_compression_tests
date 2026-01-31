export interface HomeSection {
  title: string;
  description: string;
  link: string;
  linkText: string;
  external?: boolean;
}

export interface HomeContent {
  title: string;
  description: string;
  sections: {
    [key: string]: HomeSection;
  };
}
