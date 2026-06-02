const Logistic = artifacts.require("Logistic"); // ✅

module.exports = function(deployer) {
  deployer.deploy(Logistic); // ✅ same name
};