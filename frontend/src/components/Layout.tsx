import { Outlet, NavLink } from 'react-router-dom'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  Settings,
  FileText,
  Play,
  MessageCircle,
  ScrollText,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { t, i18n } = useTranslation()
  const { isAuthEnabled, logout } = useAuth()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const navItems = [
    { path: '/dashboard', label: t('nav.dashboard'), icon: LayoutDashboard },
    { path: '/processing', label: t('nav.process'), icon: Play },
    { path: '/chat', label: t('nav.chat'), icon: MessageCircle },
    { path: '/config', label: t('nav.configuration'), icon: Settings },
    { path: '/prompts', label: t('nav.prompts'), icon: FileText },
    { path: '/logs', label: t('nav.logs'), icon: ScrollText },
  ]

  const accountControls = (
    <div className="flex gap-2">
      {(['en', 'de'] as const).map((lng) => (
        <button
          key={lng}
          onClick={() => i18n.changeLanguage(lng)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            i18n.resolvedLanguage === lng
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {t(`language.${lng}`)}
        </button>
      ))}
      {isAuthEnabled && (
        <button
          onClick={logout}
          className="ml-1 px-3 py-1 rounded-full text-sm font-medium text-gray-600 hover:bg-gray-100 flex items-center gap-1 transition-colors"
        >
          <LogOut size={14} />
          {t('login.logout')}
        </button>
      )}
    </div>
  )

  const navContent = (
    <>
      <div className="p-6">
        <div className="flex items-center gap-3 mb-1">
          <img src="/icon.png" alt="Paperless-AIssist" className="w-12 h-12 rounded" />
          <h1 className="text-xl font-bold text-gray-900">Paperless-AIssist</h1>
        </div>
        <p className="text-sm text-gray-500">{t('nav.subtitle')}</p>
      </div>
      <nav className="px-4 pb-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => setMobileNavOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  )

  return (
    <div className="min-h-screen bg-gray-50 md:flex">
      <aside className="hidden md:block w-72 bg-white border-r border-gray-200">
        {navContent}
      </aside>

      <div className="md:hidden sticky top-0 z-30 bg-white border-b border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <img src="/icon.png" alt="Paperless-AIssist" className="w-10 h-10 rounded" />
              <div className="min-w-0">
                <h1 className="text-base font-bold text-gray-900 truncate">Paperless-AIssist</h1>
                <p className="text-xs text-gray-500 truncate">{t('nav.subtitle')}</p>
              </div>
            </div>
            <button
              onClick={() => setMobileNavOpen((prev) => !prev)}
              className="p-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50"
              aria-label={mobileNavOpen ? t('common.close') : t('nav.openMenu')}
            >
              {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>
        {mobileNavOpen && <div className="border-t border-gray-200 bg-white">{navContent}</div>}
      </div>

      <div className="flex-1 flex flex-col">
        <header className="h-14 bg-white border-b border-gray-200 px-4 md:px-6 flex items-center justify-end">
          {accountControls}
        </header>
        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
