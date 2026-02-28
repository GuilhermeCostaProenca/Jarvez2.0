"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GrantedPowerFactory = void 0;
const AnalyticMind_1 = require("./AnalyticMind/AnalyticMind");
const EmptyMind_1 = require("./EmptyMind/EmptyMind");
const LinWuTradition_1 = require("./LinWuTradition/LinWuTradition");
class GrantedPowerFactory {
    static make(name) {
        return new GrantedPowerFactory.grantedPowerClasses[name]();
    }
}
exports.GrantedPowerFactory = GrantedPowerFactory;
GrantedPowerFactory.grantedPowerClasses = {
    analyticMind: AnalyticMind_1.AnalyticMind,
    emptyMind: EmptyMind_1.EmptyMind,
    linWuTradition: LinWuTradition_1.LiWuTradition,
};
