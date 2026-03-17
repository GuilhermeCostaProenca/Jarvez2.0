"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Capitalizer = void 0;
class Capitalizer {
    static capitalize(string) {
        const firstChar = string.charAt(0);
        const firstCharCapitalized = firstChar.toUpperCase();
        return `${firstCharCapitalized}${string.slice(1)}`;
    }
}
exports.Capitalizer = Capitalizer;
