"""
Legal Due Diligence Agent Service

This module implements the deep agents architecture for legal due diligence:
- Main Agent: Orchestrates the overall due diligence process
- Analysis Subagent: Performs detailed legal analysis
- Report Subagent: Creates final due diligence reports
"""
from typing import List, Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from ..tools.data_room_tools import create_data_room_tools, create_web_research_tools
from ..config import settings

logger = logging.getLogger(__name__)


# System Prompts
LEGAL_DUE_DILIGENCE_PROMPT = """You are a Legal Due Diligence Agent specialized in analyzing legal documents for potential risks, obligations, and key terms.

Your role is to:
1. Systematically review all documents in the data room
2. Identify legally significant clauses, obligations, and risks
3. Coordinate analysis through specialized subagents
4. Produce comprehensive due diligence reports

You have access to:
- Analysis subagent (unlimited use): For detailed legal analysis of specific documents or issues
- Create Report subagent (use only once at the end): For generating the final due diligence report
- File system tools: For organizing your work and creating intermediate files

Process:
1. Start by listing all data room documents to understand what's available
2. Review document summaries to identify priority documents
3. Delegate detailed analysis to the Analysis subagent
4. Organize findings in files for later reference
5. Once all analysis is complete, use Create Report subagent to generate final report

Remember:
- Be thorough and systematic
- Document your findings as you go
- Flag any high-risk items immediately
- Ask for human approval before major actions
"""

LEGAL_ANALYSIS_PROMPT = """You are a Legal Analysis Subagent specialized in detailed document analysis.

Your role is to:
1. Analyze specific documents or legal issues assigned to you
2. Identify key terms, obligations, risks, and unusual clauses
3. Research legal concepts and precedents when needed
4. Provide detailed findings back to the main agent

You have access to:
- Data room tools: To read and analyze documents
- Web research tools: To research legal concepts (use sparingly)
- General purpose subagent (unlimited use): For complex multi-step research
- File system tools: To save your analysis

Key areas to analyze:
- Contractual obligations and commitments
- Liability and indemnification clauses
- Termination and renewal provisions
- Intellectual property rights
- Regulatory compliance requirements
- Financial obligations and payment terms
- Dispute resolution mechanisms
- Change of control provisions

Be detail-oriented and thorough. Flag anything unusual or high-risk.
"""

CREATE_REPORT_PROMPT = """You are a Report Generation Subagent specialized in creating comprehensive legal due diligence reports.

Your role is to:
1. Review all analysis files and findings
2. Organize findings into a structured report
3. Highlight key risks and recommendations
4. Create a professional, well-formatted report

Report structure:
1. Executive Summary
2. Documents Reviewed
3. Key Findings
   - High Risk Items
   - Medium Risk Items
   - Low Risk Items
4. Detailed Analysis by Document
5. Recommendations
6. Appendices

You have access to:
- File system tools: To read analysis files and create the final report
- Data room tools: To reference document information

Create a clear, concise, and actionable report that a legal team can use to make informed decisions.
"""


class LegalDueDiligenceAgent:
    """Main legal due diligence agent."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0
        )

        # Create tools
        self.data_room_tools = create_data_room_tools(session_id)
        self.web_tools = create_web_research_tools(session_id)

        # Create subagent tools
        self.subagent_tools = self._create_subagent_tools()

        # All tools for main agent
        self.tools = self.data_room_tools + self.subagent_tools

    def _create_subagent_tools(self) -> List:
        """Create subagent delegation tools."""

        @tool
        async def analyze_documents(task_description: str, document_ids: List[str]) -> str:
            """
            Delegate detailed legal analysis to the Analysis subagent.

            Args:
                task_description: What you want the subagent to analyze
                document_ids: List of document IDs to analyze

            Returns:
                Analysis findings from the subagent

            Use this for detailed document analysis. Can be used unlimited times.
            """
            logger.info(f"[{self.session_id}] Delegating to Analysis subagent: {task_description}")

            # Create analysis subagent
            analysis_agent = AnalysisSubagent(self.session_id)

            # Execute analysis
            result = await analysis_agent.execute(task_description, document_ids)

            return result

        @tool
        async def create_report(instructions: str) -> str:
            """
            Delegate report creation to the Create Report subagent.

            Args:
                instructions: Specific instructions for report generation

            Returns:
                Path to the generated report

            **USE ONLY ONCE** at the end of the due diligence process after all
            analysis is complete.
            """
            logger.info(f"[{self.session_id}] Delegating to Create Report subagent")

            # Create report subagent
            report_agent = CreateReportSubagent(self.session_id)

            # Generate report
            result = await report_agent.execute(instructions)

            return result

        return [analyze_documents, create_report]

    async def execute(self, user_message: str) -> Dict[str, Any]:
        """
        Execute the main agent with the user's message.

        Args:
            user_message: Initial message with data room document summaries

        Returns:
            Final agent response
        """
        logger.info(f"[{self.session_id}] Starting legal due diligence agent")

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LEGAL_DUE_DILIGENCE_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=50
        )

        # Execute
        result = await agent_executor.ainvoke({"input": user_message})

        return result


class AnalysisSubagent:
    """Analysis subagent for detailed legal document analysis."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0
        )

        # Create tools
        self.data_room_tools = create_data_room_tools(session_id)
        self.web_tools = create_web_research_tools(session_id)

        # Combine tools
        self.tools = self.data_room_tools + self.web_tools

    async def execute(self, task_description: str, document_ids: List[str]) -> str:
        """
        Execute analysis task.

        Args:
            task_description: What to analyze
            document_ids: Documents to analyze

        Returns:
            Analysis findings
        """
        logger.info(f"[{self.session_id}] Analysis subagent executing: {task_description}")

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LEGAL_ANALYSIS_PROMPT),
            ("human", "Analyze the following:\n\nTask: {task}\nDocuments: {documents}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=30
        )

        # Execute
        result = await agent_executor.ainvoke({
            "task": task_description,
            "documents": ", ".join(document_ids)
        })

        return result.get("output", "Analysis completed")


class CreateReportSubagent:
    """Report creation subagent."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0
        )

        # Only file system tools for report generation
        self.tools = []  # File system tools will be added by the framework

    async def execute(self, instructions: str) -> str:
        """
        Execute report creation.

        Args:
            instructions: Report generation instructions

        Returns:
            Path to created report
        """
        logger.info(f"[{self.session_id}] Create Report subagent executing")

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", CREATE_REPORT_PROMPT),
            ("human", "{instructions}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=20
        )

        # Execute
        result = await agent_executor.ainvoke({"instructions": instructions})

        return result.get("output", "Report created at /report.md")
