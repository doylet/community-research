export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome</h1>
        <p className="text-xl text-gray-600">This is a simple website with a landing page and an about page.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-gray-50 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-3">What we do</h2>
          <p className="text-gray-600">We provide simple solutions for your needs.</p>
        </div>

        <div className="bg-gray-50 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-3">Get in touch</h2>
          <p className="text-gray-600">Contact us to learn more about our services.</p>
        </div>
      </div>
    </div>
  )
}
