import Image from 'next/image'

export default function WabiSabiBackground() {
  return (
    <div className="fixed inset-0 -z-10 h-screen w-full overflow-hidden bg-[#f0f0f0] dark:bg-[#1a1a1a]">
      <Image
        src="/static/images/wabi-sabi-bg.png"
        alt="Wabi Sabi Background"
        fill
        className="object-cover opacity-10 mix-blend-multiply dark:opacity-20 dark:mix-blend-soft-light"
        priority
      />
      <div className="absolute inset-0 bg-gradient-to-b from-white/50 to-transparent dark:from-black/50" />
    </div>
  )
}
