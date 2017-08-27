from moose.apps import AppConfig

# from cityscape import actions

class CityscapeConfig(AppConfig):
    name = 'cityscape'

    def initialize(self):
        self.register('Upload', 'upload', default=True)
        self.register('Export', 'export')
        self.register('Export', 'review', entry='review')

    def register(self, action_klass, action_alias, default=False, entry=None)
        pass
