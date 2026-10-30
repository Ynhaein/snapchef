import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Something went wrong.' }
  }
  render() {
    if (this.state.hasError) {
      return (
        <main className="page-shell">
          <p role="alert" className="scan-error">{this.state.message}</p>
          <button className="proof-button proof-button-quiet" onClick={() => this.setState({ hasError: false, message: '' })}>
            Try again
          </button>
        </main>
      )
    }
    return this.props.children
  }
}
