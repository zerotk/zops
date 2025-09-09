from zerotk import deps

# myapp.services.Service
@deps.define()
class Service:
  value: str = ""

# myapp.services.OtherService
@deps.define()
class OtherService(Service):
  pass

# myapp.verticals.say_hi
@deps.inject
def say_hi(self: Service) -> Service:
  self.value = "hi"
  return self

# myapp.verticals.say_hi
@deps.inject
def say_bye(self: OtherService) -> Service:
  self.value = "bye"
  return self

# main
a = Service()
assert a.say_hi() is a
assert a.value == "hi"
assert not hasattr(a, "say_bye")

b = OtherService()
assert b.say_hi().say_bye() is b
assert b.value == "bye"
