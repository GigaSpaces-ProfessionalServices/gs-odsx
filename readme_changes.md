Fixed below object management issues :
- On service creation please use 3 manager for locators not only 1.
- Removed gs.username, gs.password from the service param.
- On register type if type already exist in space it should indicate it and not act as it was successfully registered.
- Removed validation option from UI