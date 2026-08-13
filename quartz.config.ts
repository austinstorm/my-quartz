import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz 4 Configuration
 *
 * See https://quartz.jzhao.xyz/configuration for more information.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "Austin Storm's Commonplace Book",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: {
      provider: "plausible",
    },
    locale: "en-US",
    baseUrl: "quartz.jzhao.xyz",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      // fontOrigin "local" means the site uses system fonts. The actual body/
      // header fonts (the Transitional stack) are set in quartz/styles/custom.scss.
      // The typography names below are only used to render OG social-preview
      // images, so they must be Google Fonts.
      fontOrigin: "local",
      cdnCaching: true,
      typography: {
        header: "Schibsted Grotesk",
        body: "Source Sans Pro",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#DFD4C3",
          lightgray: "#CDBFAA",
          gray: "#3E5974",
          darkgray: "#4D4C4B",
          dark: "#4D4C4B",
          secondary: "#5D5646",
          tertiary: "#A07D54",
          highlight: "rgba(93, 86, 70, 0.15)",
          textHighlight: "rgba(160, 125, 84, 0.35)",
        },
        darkMode: {
          light: "#211D16",
          lightgray: "#38332B",
          gray: "#8B97A8",
          darkgray: "#D9CDB9",
          dark: "#EFE7D9",
          secondary: "#A07D54",
          tertiary: "#C4A57E",
          highlight: "rgba(160, 125, 84, 0.2)",
          textHighlight: "rgba(196, 165, 126, 0.35)",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
      // Comment out CustomOgImages to speed up build time
      Plugin.CustomOgImages(),
    ],
  },
}

export default config
