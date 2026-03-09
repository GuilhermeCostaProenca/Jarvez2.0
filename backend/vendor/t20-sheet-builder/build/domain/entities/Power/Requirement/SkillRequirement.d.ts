import type { SheetInterface } from '../../Sheet/SheetInterface';
import type { SkillName } from '../../Skill/SkillName';
import { Requirement } from './Requirement';
export declare class SkillRequirement extends Requirement {
    readonly skill: SkillName;
    readonly description: string;
    constructor(skill: SkillName);
    verify(sheet: SheetInterface): boolean;
    protected getDescription(): string;
}
