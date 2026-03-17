import type { SpellStatic } from './SpellStatic';
import { type SpellSchool } from './SpellSchool';
export declare class Spells {
    static getAll(): SpellStatic[];
    static getAllArcane(): SpellStatic[];
    static getAllDivine(): SpellStatic[];
    static getBySchool(school: SpellSchool): SpellStatic[];
}
