import time
# import sys
# import traceback

class Context:
    def __init__(self, dialog, entities, history, counter, max_depth=30, history_restart_minutes=30):
        self.counter = counter
        self.entities = entities
        self.history = history
        self.max_depth = max_depth
        self.dialog = dialog
        self.history_restart_minutes = history_restart_minutes

    def add(self, new_entities):
        if new_entities is None:
            return
        self.counter += 1

        # add all new entities
        for entity,values in new_entities.items():
            if entity not in self.entities:
                self.entities[entity] = []
            # allow also direct passing of {'entity' : 'value'}
            if not isinstance(values, dict) and not isinstance(values, list):
                values = {'value':values}
            if not isinstance(values, list):
                values = [values]
            # prepend each value to start of the list with 0 age 
            for value in values:
                self.dialog.log.info('Entity %s: %s' % (entity, value['value']))
                value['counter'] = self.counter
                self.entities[entity] = [value] + self.entities[entity]

    def add_state(self, state_name):
        timestamp = int(time.time())
        if self.history:
            previous = self.history[-1]['timestamp']
            minutes = (timestamp - previous)/60
            if minutes > self.history_restart_minutes:
                self.dialog.log.info('Restarting history after {} minutes of inactivity'.format(int(minutes)))
                self.history = []

        state = {
            'name' : state_name,
            'timestamp' : timestamp
        }
        self.history.append(state)

    def get_history_state(self, index):
        return self.history[index] if len(self.history) >= abs(index) else None

    def get_history_string(self, index=None):
        return ','.join([state['name'] for state in self.history[0:index]])

    def get_all(self, entity, max_age=None, limit=None, key='value'):
        values = []
        if entity not in self.entities:
            return values
        for value in self.entities[entity]:
            age = self.counter-value['counter']
            # if I found a too old value, stop looking
            if max_age is not None and age > max_age:
                break
            # if I already have enough values, stop looking
            if limit is not None and len(values) >= limit:
                break
            values.append(value[key] if key else value)
        return values 

    def get_age(self, entity, max_age=None, key='value'):
        value = self.get_all(entity, max_age=max_age, limit=1, key=key)
        counter = self.get_all(entity, max_age=max_age, limit=1, key='counter')
        if not value:
            return (None, None)
        return value[0],self.counter-counter[0] 
    
    def get(self, entity, max_age=None, key='value'):
        values = self.get_all(entity, max_age=max_age, limit=1, key=key)
        if not values:
            return None
        return values[0]

    def set(self, entity, value_dict):
        if not isinstance(value_dict, dict):
            raise ValueError('Use a dict to set a context value, e.g. {"value":"foo"}')
        if entity not in self.entities:
            self.entities[entity] = []
        value_dict['counter'] = self.counter
        self.entities[entity] = [value_dict]+self.entities[entity][:self.max_depth-1]

    def has_any(self, entities, max_age=None):
        for entity in entities:
            if self.get(entity, max_age=max_age):
                return True
        return False
    #def entity_value(self, entity):
    #    values = self.entity_values(entity)
    #    return values[0] if values else None

    #def __str__(self):
    #    res = "Message: %s\n" % (self.text)
    #    for entity in self.entities:
    #        for value in self.entities[entity]:
    #            res += "Entity %s: %s (%s)\n" % (entity, value['value'], value['confidence'])