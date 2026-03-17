import { type Spell } from './Spell';
import { type SpellName } from './SpellName';
import { type SpellStatic } from './SpellStatic';
export declare class SpellFactory {
    static readonly map: Record<SpellName, SpellStatic>;
    static make(name: SpellName): Spell;
}
