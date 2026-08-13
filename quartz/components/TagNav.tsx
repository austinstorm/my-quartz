import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { FullSlug, resolveRelative } from "../util/path"
import { classNames } from "../util/lang"

interface Options {
  title?: string
}

const defaultOptions: Options = {
  title: "All Tags",
}

export default ((userOpts?: Partial<Options>) => {
  const TagNav: QuartzComponent = ({
    allFiles,
    fileData,
    displayClass,
  }: QuartzComponentProps) => {
    const opts = { ...defaultOptions, ...userOpts }

    const distinctTags = new Set<string>()
    for (const file of allFiles) {
      for (const tag of file.frontmatter?.tags ?? []) {
        distinctTags.add(tag)
      }
    }

    return (
      <div class={classNames(displayClass, "tag-nav")}>
        <ul>
          <li>
            <a class="internal" href={resolveRelative(fileData.slug!, "all-tags" as FullSlug)}>
              {opts.title}
            </a>
            <span class="tag-count">{distinctTags.size}</span>
          </li>
        </ul>
      </div>
    )
  }

  TagNav.css = `
    .tag-nav ul {
      list-style: none;
      margin: 0.5rem 0 0 0;
      padding-left: 0;
    }
    .tag-nav li {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 0.15rem 0;
    }
    .tag-nav li > a {
      color: var(--dark);
      opacity: 0.75;
      background-color: transparent;
    }
    .tag-nav li > a:hover {
      color: var(--tertiary);
      opacity: 1;
    }
    .tag-nav .tag-count {
      color: var(--gray);
      font-size: 0.8rem;
      opacity: 0.7;
    }
  `

  return TagNav
}) satisfies QuartzComponentConstructor
