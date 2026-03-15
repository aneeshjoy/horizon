import { Network, Info } from 'lucide-react'
import type { MQTTConfig as MQTTConfigType } from '@/api/types'
import { Tooltip } from '@/components/ui/Tooltip'
import { useMQTTStatus } from '@/hooks/useMQTTStatus'

interface MQTTConfigProps {
  config: MQTTConfigType
  onChange: (config: MQTTConfigType) => void
}

export function MQTTConfig({ config, onChange }: MQTTConfigProps) {
  const { status } = useMQTTStatus()

  const updateConfig = <K extends keyof MQTTConfigType>(field: K, value: MQTTConfigType[K]) => {
    onChange({ ...config, [field]: value })
  }

  const toggleCamera = (camera: string) => {
    const cameras = config.enabled_cameras || []
    if (cameras.includes(camera)) {
      updateConfig('enabled_cameras', cameras.filter(c => c !== camera))
    } else {
      updateConfig('enabled_cameras', [...cameras, camera])
    }
  }

  const availableCameras = status?.detected_cameras || []
  const connectionStatus = status?.connected ? 'Connected' : status?.running ? 'Disconnected' : 'Stopped'

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="rounded-full p-2 bg-green-500/10">
          <Network className="h-5 w-5 text-green-500" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-semibold">MQTT Configuration</h2>
          <p className="text-sm text-muted-foreground">
            Connect to Frigate MQTT broker for real-time license plate updates
          </p>
        </div>
        {status && (
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${status.connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-muted-foreground">{connectionStatus}</span>
          </div>
        )}
      </div>

      <div className="space-y-6">
        {/* Enable/Disable */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Enable MQTT Integration</label>
            <Tooltip content="Connect to Frigate MQTT broker for real-time license plate detection" />
          </div>
          <button
            onClick={() => updateConfig('enabled', !config.enabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.enabled ? 'bg-primary' : 'bg-input'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                config.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Connection Settings */}
        <div className="space-y-4 pt-4 border-t">
          <h3 className="text-sm font-medium">Connection Settings</h3>

          {/* Broker Host */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Broker Host</label>
              <Tooltip content="MQTT broker hostname or IP address (e.g., localhost or 192.168.1.100)" />
            </div>
            <input
              type="text"
              value={config.broker_host}
              onChange={(e) => updateConfig('broker_host', e.target.value)}
              placeholder="localhost"
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Broker Port */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Broker Port</label>
              <Tooltip content="MQTT broker port (default: 1883)" />
            </div>
            <input
              type="number"
              min="1"
              max="65535"
              value={config.broker_port}
              onChange={(e) => updateConfig('broker_port', parseInt(e.target.value) || 1883)}
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Client ID */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Client ID</label>
              <Tooltip content="Unique identifier for this MQTT client" />
            </div>
            <input
              type="text"
              value={config.client_id}
              onChange={(e) => updateConfig('client_id', e.target.value)}
              placeholder="horizon-lpr"
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Topic Prefix */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Topic Prefix</label>
              <Tooltip content="Frigate MQTT topic prefix (default: frigate)" />
            </div>
            <input
              type="text"
              value={config.topic_prefix}
              onChange={(e) => updateConfig('topic_prefix', e.target.value)}
              placeholder="frigate"
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Authentication */}
        <div className="space-y-4 pt-4 border-t">
          <h3 className="text-sm font-medium">Authentication (Optional)</h3>

          {/* Username */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Username</label>
              <Tooltip content="MQTT username (leave empty if no authentication)" />
            </div>
            <input
              type="text"
              value={config.username || ''}
              onChange={(e) => updateConfig('username', e.target.value || null)}
              placeholder="Not set"
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Password */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <label className="text-sm font-medium">Password</label>
              <Tooltip content="MQTT password (leave empty if no authentication)" />
            </div>
            <input
              type="password"
              value={config.password || ''}
              onChange={(e) => updateConfig('password', e.target.value || null)}
              placeholder="Not set"
              className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Timezone */}
        <div className="space-y-2 pt-4 border-t">
          <div className="flex items-center gap-1.5">
            <label className="text-sm font-medium">Timezone</label>
            <Tooltip content="Local timezone for timestamp conversion" />
          </div>
          <select
            value={config.timezone}
            onChange={(e) => updateConfig('timezone', e.target.value)}
            className="w-full px-3 py-2 text-sm border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="America/Los_Angeles">Pacific Time (US)</option>
            <option value="America/Denver">Mountain Time (US)</option>
            <option value="America/Chicago">Central Time (US)</option>
            <option value="America/New_York">Eastern Time (US)</option>
            <option value="Europe/London">GMT / UK</option>
            <option value="Europe/Paris">Central European</option>
            <option value="Europe/Berlin">Central European (Germany)</option>
            <option value="Europe/Berlin">Central European (Germany)</option>
            <option value="Asia/Tokyo">Japan</option>
            <option value="Australia/Sydney">Australia (Sydney)</option>
            <option value="Pacific/Auckland">New Zealand</option>
            <option value="UTC">UTC</option>
          </select>
        </div>

        {/* Camera Filtering */}
        <div className="space-y-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Camera Filtering</h3>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-sm">
                <input
                  type="radio"
                  checked={config.enabled_cameras_mode === 'whitelist'}
                  onChange={() => updateConfig('enabled_cameras_mode', 'whitelist')}
                  className="w-4 h-4"
                />
                Whitelist
              </label>
              <label className="flex items-center gap-1 text-sm">
                <input
                  type="radio"
                  checked={config.enabled_cameras_mode === 'blacklist'}
                  onChange={() => updateConfig('enabled_cameras_mode', 'blacklist')}
                  className="w-4 h-4"
                />
                Blacklist
              </label>
            </div>
          </div>

          {availableCameras.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                {config.enabled_cameras_mode === 'whitelist'
                  ? 'Only process readings from selected cameras'
                  : 'Process readings from all cameras except selected'}
                {config.enabled_cameras.length === 0 && ' (empty = all cameras)'}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {availableCameras.map((camera) => (
                  <label key={camera} className="flex items-center gap-2 text-sm p-2 border rounded-md cursor-pointer hover:bg-muted/50">
                    <input
                      type="checkbox"
                      checked={config.enabled_cameras.includes(camera)}
                      onChange={() => toggleCamera(camera)}
                      className="w-4 h-4"
                    />
                    {camera}
                  </label>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              No cameras detected yet. Connect to MQTT to discover cameras.
            </p>
          )}
        </div>

        {/* Connection Status */}
        {status && (
          <div className="pt-4 border-t">
            <h3 className="text-sm font-medium mb-3">Connection Status</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Status:</span>{' '}
                <span className={status.connected ? 'text-green-600' : 'text-red-600'}>
                  {connectionStatus}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Messages:</span>{' '}
                <span>{status.messages_received} received</span>
              </div>
              <div>
                <span className="text-muted-foreground">Processed:</span>{' '}
                <span>{status.messages_processed}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Uptime:</span>{' '}
                <span>{status.uptime_seconds ? `${Math.floor(status.uptime_seconds / 60)}m` : '-'}</span>
              </div>
            </div>
            {status.error_message && (
              <p className="mt-2 text-xs text-red-600">{status.error_message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
