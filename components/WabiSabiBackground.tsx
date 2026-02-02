import Image from 'next/image'
import bgImage from '../public/static/images/wabi-sabi-bg.webp'

export default function WabiSabiBackground() {
  return (
    <div className="fixed inset-0 -z-10 h-screen w-full overflow-hidden bg-[#f0f0f0] dark:bg-[#1a1a1a]">
      <Image
        src={bgImage}
        alt="Wabi Sabi Background"
        placeholder="blur"
        fill
        sizes="100vw"
        className="opacity-1 object-cover mix-blend-multiply dark:opacity-20 dark:mix-blend-soft-light"
        priority
      />
      <div className="absolute inset-0 bg-gradient-to-b from-white/50 to-transparent dark:from-black/50" />
    </div>
  )
}
