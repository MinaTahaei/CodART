from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled


class MakeFieldNonStaticRefactoringListener(JavaParserLabeledListener):
    """
    To implement the encapsulate filed refactored
    Encapsulate field: Make a public field private and provide accessors
    """

    def __init__(self, common_token_stream: CommonTokenStream = None,
                 field_identifier: str = None, class_identifier: str = None, package_identifier: str = None):
        """
        :param common_token_stream:
        """
        self.token_stream = common_token_stream
        self.field_identifier = field_identifier
        self.class_identifier = class_identifier
        self.package_identifier = package_identifier
        self.declared_objects_names = []

        self.is_package_imported = False
        self.in_selected_package = False
        self.in_selected_class = False
        self.in_some_package = False
        self.class_start_index = 0
        self.canceled = False

        self.placeholder_field_identifier = "placeholder"

        # Move all the tokens in the source code in a buffer, token_stream_rewriter.
        if common_token_stream is not None:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)
        else:
            raise TypeError('common_token_stream is None')

    def enterPackageDeclaration(self, ctx: JavaParserLabeled.PackageDeclarationContext):
        self.in_some_package = True
        if self.package_identifier is not None:
            if self.package_identifier == ctx.qualifiedName().getText():
                self.in_selected_package = True
                print("Package Found")

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):

        if self.package_identifier is None and not self.in_some_package or \
                self.package_identifier is not None and self.in_selected_package:
            if ctx.IDENTIFIER().getText() == self.class_identifier:
                print("Class Found")
                self.in_selected_class = True

    def enterImportDeclaration(self, ctx: JavaParserLabeled.ImportDeclarationContext):
        if self.package_identifier is not None:
            if ctx.getText() == "import" + self.package_identifier + "." + self.class_identifier + ";" \
                    or ctx.getText() == "import" + self.package_identifier + ".*" + ";" \
                    or ctx.getText() == "import" + self.package_identifier + ";":
                self.is_package_imported = True

    def exitFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        if self.package_identifier is None and not self.in_some_package \
                or self.package_identifier is not None and self.in_selected_package:
            if self.in_selected_class:
                if ctx.variableDeclarators().variableDeclarator(0) \
                        .variableDeclaratorId().getText() == self.field_identifier:

                    grand_parent_ctx = ctx.parentCtx.parentCtx

                    if len(grand_parent_ctx.modifier()) > 0:
                        for i in range(len(grand_parent_ctx.modifier())):
                            if grand_parent_ctx.modifier(i).getText() == "static":
                                self.token_stream_rewriter.replaceIndex(index=grand_parent_ctx.start.tokenIndex + i,
                                                                        text=" ")
                                break

        if self.package_identifier is None or self.package_identifier is not None and self.is_package_imported:
            if ctx.typeType().classOrInterfaceType() is not None:
                if ctx.typeType().classOrInterfaceType().getText() == self.class_identifier:
                    self.declared_objects_names.append(ctx.variableDeclarators().variableDeclarator(0)
                                                       .variableDeclaratorId().getText())
                    print("Object " + ctx.variableDeclarators().variableDeclarator(0).variableDeclaratorId().getText() \
                          + " of type " + self.class_identifier + " found.")

    def enterExpression1(self, ctx: JavaParserLabeled.Expression1Context):
        if self.is_package_imported or self.package_identifier is None or self.in_selected_package:
            if ctx.getText() == self.class_identifier + "." + self.field_identifier:
                if len(self.declared_objects_names) == 0:
                    print("No object found...canceling ")
                    self.canceled = True
                    return
                self.token_stream_rewriter.replaceIndex(
                    index=ctx.start.tokenIndex,
                    text=self.declared_objects_names[0])
