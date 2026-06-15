'use client'
import type { FC } from 'react'
import { cn } from '@langgenius/data-ui/cn'
import useTheme from '@/hooks/use-theme'
import { basePath } from '@/utils/var'

export type LogoStyle = 'default' | 'monochromeWhite'

export const logoPathMap: Record<LogoStyle, string> = {
  default: '/logo/logo.svg',
  monochromeWhite: '/logo/logo-monochrome-white.svg',
}

export type LogoSize = 'large' | 'medium' | 'small'

export const logoSizeMap: Record<LogoSize, string> = {
  large: 'w-20 h-7',
  medium: 'w-16 h-[22px]',
  small: 'w-12 h-4',
}

type DataLogoProps = {
  style?: LogoStyle
  size?: LogoSize
  className?: string
  alt?: string
}

const DataLogo: FC<DataLogoProps> = ({
  style = 'default',
  size = 'medium',
  className,
  alt = 'DATA logo',
}) => {
  const { theme } = useTheme()
  const themedStyle = (theme === 'dark' && style === 'default') ? 'monochromeWhite' : style

  return (
    <img
      src={`${basePath}${logoPathMap[themedStyle]}`}
      className={cn('block object-contain', logoSizeMap[size], className)}
      alt={alt}
    />
  )
}

export default DataLogo
