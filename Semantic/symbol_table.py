class SymbolTable:
    def __init__(self):
        # Stack of scopes. Each scope is a dictionary.
        # Index 0 is Global Scope.
        self.scopes = [{}] 

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def define(self, name, type_info, category="var"):
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False
        current_scope[name] = {
            "type": type_info,
            "category": category, 
            "value": None
        }
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None