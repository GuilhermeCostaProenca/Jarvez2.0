import { type Context } from '../Context';
import { type ContextualModifierInterface } from '../Modifier/ContextualModifier/ContextualModifierInterface';
import { type ModifierInterface } from '../Modifier/ModifierInterface';
import { type SkillName } from '../Skill';
import { type Skill } from '../Skill/Skill';
import { type SerializedSheetSkills } from './SerializedSheet/SerializedSheetInterface';
import { type SheetInterface } from './SheetInterface';
import { type SheetSkillsInterface } from './SheetSkillsInterface';
export declare class SheetSkills implements SheetSkillsInterface {
    private readonly skills;
    readonly intelligenceSkills: SkillName[];
    constructor(skills?: Record<SkillName, Skill>);
    trainSkill(name: SkillName): void;
    getSkill(name: SkillName): Skill;
    addContextualModifierTo(skill: SkillName, modifier: ContextualModifierInterface): void;
    addFixedModifierTo(skill: SkillName, modifier: ModifierInterface): void;
    trainIntelligenceSkills(skills: SkillName[]): void;
    getSkills(): Record<SkillName, Skill>;
    serialize(sheet: SheetInterface, context: Context): SerializedSheetSkills;
}
