import type { SkillName } from '../../Skill/SkillName';
import type { Spell } from '../../Spell/Spell';
import { Arcanist } from './Arcanist';
import type { ArcanistPath } from './ArcanistPath/ArcanistPath';
export declare class ArcanistBuilder {
    static chooseSkills(skills: SkillName[][]): {
        choosePath: (path: ArcanistPath) => {
            chooseSpells: (spells: Spell[]) => Arcanist<ArcanistPath>;
        };
    };
    private static choosePath;
    private static chooseSpells;
}
