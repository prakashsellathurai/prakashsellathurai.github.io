'use client'

import { Popover, PopoverButton, PopoverPanel, Transition } from '@headlessui/react'
import { ReactNode, useState, useRef } from 'react'
import { Fragment } from 'react'

interface SideNoteProps {
  children: ReactNode
  title?: string
}

export default function SideNote({ children, title = 'Note' }: SideNoteProps) {
  const [isOpen, setIsOpen] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setIsOpen(true)
  }

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsOpen(false)
    }, 200) // Small delay to allow moving to the panel
  }

  return (
    <Popover
      as="span"
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <PopoverButton
        as="button"
        className="cursor-help rounded-sm font-medium text-primary-500 underline decoration-primary-300 decoration-dashed underline-offset-4 hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
      >
        {title}
      </PopoverButton>

      <Transition
        show={isOpen}
        as={Fragment}
        enter="transition ease-out duration-200"
        enterFrom="opacity-0 translate-y-1"
        enterTo="opacity-100 translate-y-0"
        leave="transition ease-in duration-150"
        leaveFrom="opacity-100 translate-y-0"
        leaveTo="opacity-0 translate-y-1"
      >
        <PopoverPanel
          static
          as="span"
          className="absolute left-1/2 z-50 mt-2 w-64 max-w-[90vw] -translate-x-1/2 transform sm:w-72 md:w-80"
        >
          <span
            className="block overflow-hidden rounded-lg shadow-xl ring-1 ring-black ring-opacity-5"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <span className="block border-l-4 border-primary-500 bg-white p-4 text-sm leading-6 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {children}
            </span>
          </span>
        </PopoverPanel>
      </Transition>
    </Popover>
  )
}
